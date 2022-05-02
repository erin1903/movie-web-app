$("#movie_name").keyup(function(event) {
    if (event.keyCode === 13) {
        $("#user_input").click();
    }
});

//calls to flask and returns TMDB ids of movies that are present in our database based on user input
function csvCheck(){
    $("#loader").fadeIn();
    $("#suggestions").html("");
    $("#movie_container").html("");
    var user_input = $("#movie_name").val().trim();
    if(!user_input){
        $("#loader").css('display','none');
        $("#suggestions").append("<p class=\"text-danger text-center\">Please enter your movie.</p>");
        $('#suggestions_container').css('display','block');
    }
    else{
        $.ajax({
            url: "/suggestions",
            type: "POST",
            data: {"user_input":user_input},
            success: function(data){
                $("#loader").css('display','none');
                if(data.length == 0){
                    $("#suggestions").append("<p class=\"text-danger text-center\">Sorry, the requested movie is not in our database!</p>");
                    $('#suggestions_container').css('display','block');
                }
                else{
                    showResults(data);
                    $('#suggestions_container').css('display','block');
                }
            },
            error: function(xhr, textStatus, error){
                $("#loader").delay(500).fadeOut();
                alert("An error occurred while connecting to the server");
            }
        });
    }
}

//displays results of search
function showResults(movie_search_list){
    let {m_info, err} = tmdbReq(movie_search_list); //get titles and poster paths of suggested movies
    if(err.length != 0){ //if error occurred while querying for titles and posters, delete that movie
        for(var er = err.length - 1; er >= 0; er--){
            movie_search_list.splice(err[er],1);
        }
    }
    $.each(movie_search_list, function(index, m_id){
        $(`<div class="col-6 col-md-4 col-lg-3 col-xl-2">
            <div class="card mb-5 card-hover-shadow" style="border-radius: 20px;" id="${m_id}"
            title="${m_info[index][0]}" onclick="clickCard(this)">
                <div class="bg-image img-hover-zoom" style="border-radius: 20px;">
                    <img class="card-img-top" style="border-radius: 20px;" src="${m_info[index][1]}" alt="">
                </div>
                <div class="card-body">
                    <h5 class="card-title">${m_info[index][0]}</h5>
                </div>
            </div>
        </div>`).appendTo("#suggestions");
    });
}

//calls to TMDB and returns title and poster path of a list of TMDB ids
function tmdbReq(movie_search_list){
    var API_KEY = "YOUR_API_KEY";
    var BASE_URL_IMG = "https://image.tmdb.org/t/p/w185";
    m_info = [];
    err = [];
    $.each(movie_search_list, function(index, m_id){
        $.ajax({
        url: "https://api.themoviedb.org/3/movie/"+m_id+"?api_key="+API_KEY+"&language=en-US",
        type: "GET",
        async: false,
        success: function(data){
            img_path = BASE_URL_IMG + data.poster_path;
            m_info.push([data.title, img_path]);
        },
        error: function(xhr, textStatus, error){
            $("#loader").delay(500).fadeOut();
            err.push(index);
        }
        });
    });
    return {m_info, err}
}

//invoked when clicked on a movie card
function clickCard(e){
    var movie_title = e.getAttribute("title");
    var movie_id = e.getAttribute("id");
    getRec(movie_id, movie_title);
}

//calls to flask and returns TMDB ids of recommended movies to the clicked movie
function getRec(movie_id, movie_title){
    $('#suggestions_container').css('display','none');
    $('#movie_container').css('display','none');
    $("#loader").fadeIn();
    $.ajax({
        url: "/recommendations",
        type: "POST",
        data: {"movie_id":movie_id},
        success: function(data){
            tmdbReqMoreDetails(movie_id, data);
        },
        error: function(xhr, textStatus, error){
            $("#loader").delay(500).fadeOut();
            alert("An error occurred while getting recommendations for "+movie_title);
        }
    });
}

//calls to TMDB and returns detailed information of the clicked movie
function tmdbReqMoreDetails(movie_id, movie_rec){
    var API_KEY = "YOUR_API_KEY";
    $.ajax({
        url: "https://api.themoviedb.org/3/movie/"+movie_id+"?api_key="+API_KEY+"&language=en-US",
        type: "GET",
        success: function(data){
            credits(data, movie_rec, movie_id, API_KEY);
        },
        error: function(xhr, textStatus, error){
            $("#loader").delay(500).fadeOut();
            alert("An error in receiving information form database!");
        }
    });
}

//calls to TMDB and returns actors and director of the clicked movie
function credits(movie_info, movie_rec, movie_id, API_KEY){
    actors = [];
    $.ajax({
        url: "https://api.themoviedb.org/3/movie/"+movie_id+"/credits?api_key="+API_KEY+"&language=en-US",
        type: "GET",
        success: function(data){
            for(var actor in [...Array(5).keys()]){ //top 5 actors
                try {
                actors.push(data.cast[actor].name);
                }
                catch(err){
                continue;
                }
            }
            for(var i in [...Array(data.crew.length).keys()]){
                if(data.crew[i].job == "Director"){
                    director = data.crew[i].name;
                    break;
                }
            }
            credits = {"actors":actors, "director":director};
            toFlask(movie_info, movie_rec, credits);
        },
        error: function(xhr, textStatus, error){
            $("#loader").delay(500).fadeOut();
            alert("An error in receiving information form database!")
        }
    });
}

//sends every movie information to flask and redirects the user to movie page
function toFlask(movie_info, movie_rec, credits){
    var BASE_URL_IMG = "https://image.tmdb.org/t/p/w185";
    var my_genres = [];
    for (var gen in movie_info.genres){
        my_genres.push(movie_info.genres[gen].name);
    }
    let {rec_m_info, err} = infoRecM(movie_rec, BASE_URL_IMG);
    if(err.length != 0){    //if some error occurred while retrieving title and poster, delete that movie
        for(var er = err.length - 1; er >= 0; er--){
            movie_rec.splice(err[er],1);
        }
    }
    movie_info["movie_poster_path"] = BASE_URL_IMG + movie_info.poster_path;
    movie_info['release_date'] = new Date(movie_info.release_date).getFullYear();
    movie_info["genres"] = my_genres.join(", ");
    movie_info['director'] = JSON.stringify(credits.director);
    movie_info['actors'] = credits.actors.join(", ");
    movie_info["rec_movies"] = JSON.stringify(movie_rec);
    movie_info["rec_m_info"] = JSON.stringify(rec_m_info);
    $.ajax({
        url: "/",
        type: "POST",
        data: movie_info,
        complete: function(data){
            $("#loader").delay(500).fadeOut();
        },
        success: function(data){
            window.location.href = "movie";
        },
        error: function(xhr, textStatus, error){
            $("#suggestions").append("<p class=\"text-danger text-center\">Sorry, something went wrong at our end!</p>");
        }
    });
}

// calls to flask and returns titles and poster paths of recommended movies
function infoRecM(movie_rec, BASE_URL_IMG){
    var API_KEY = "YOUR_API_KEY";
    rec_m_info = [];
    err = [];
    for(m in movie_rec){
        $.ajax({
            url: "https://api.themoviedb.org/3/movie/"+movie_rec[m]+"?api_key="+API_KEY+"&language=en-US",
            type: "GET",
            async: false,
            success: function(data){
                    img_path = BASE_URL_IMG + data.poster_path;
                    var info = [img_path, data.title];
                    rec_m_info.push(info); //contains abs src, title
            },
            error: function(xhr, textStatus, error){
                err.push(m);
            }
        });
    }
    return {rec_m_info, err};
}
