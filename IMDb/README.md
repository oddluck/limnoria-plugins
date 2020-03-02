Information about IMDb titles from the OMDB API.

Obtain an [OMDB API Key](https://omdbapi.com/apikey.aspx)

`config plugins.imdb.omdbAPI your_key_here`

`config plugins.imdb.googleSearch True/False` enable/disable google searches 

`config plugins.imdb.template` change the reply template

Default template:
 
`\x02\x031,8 IMDb \x0F\x02 :: $title ($year, $country, [$rated], $genre, $runtime) :: IMDb: $imdbRating | MC: $metascore | RT: $tomatoMeter :: http://imdb.com/title/$imdbID :: $plot :: Director: $director :: Cast: $actors :: Writer: $writer`

Variable       | Description
---------------|------------
title          | Movie title
year           | Release year
country        | Country
director       | Director
plot           | Plot
imdbID         | IMDB tile ID#
imdbRating     | IMDB rating
metascore      | Metacritic score
released       | Release date
genre          | Genre
awards         | Awards won
actors         | Actors
rated          | Rating
runtime        | Runtime
writer         | Writer
votes          | Votes
website        | Website URL
language       | Language
boxOffice      | Box Office
production     | Production company
poster         | Poster URL
