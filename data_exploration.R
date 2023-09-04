library(tidyverse)
library(ggmap)
library(tidygeocoder)
library(rgdal)
library(rgeos)
library(extrafont)
library(ggspatial)
library(ggthemes)
library(sf)
library(geosphere)
library(OpenStreetMap)
library(patchwork)


#Loading the Files
chi_map <- read_sf("https://raw.githubusercontent.com/thisisdaryn/data/master/geo/chicago/Comm_Areas.geojson") 
train_map <- read_sf("train_stations/CTARailLines.shp")
apt_data <- read_csv("scraped_apartment_results1129.csv")


##Pipe to pull out cost, beds, per person cost, and zipcodes
clean_apt_data <- apt_data %>%
  mutate(cost = as.numeric(parse_number(cost))) %>%
  mutate(beds = as.numeric(parse_number(beds))) %>%
  mutate(baths = as.numeric(parse_number(baths))) %>%
  mutate(sqft = as.numeric(parse_number(sqft))) %>%
  drop_na(beds, cost, baths, sqft) %>%
  mutate(pp_cost = cost/beds) %>%
  mutate(neighborhood = as.factor(neighborhood)) %>%
  rowwise() %>%
  mutate(zip = as.numeric(last(str_split(zipcode, " ")[[1]]))) %>%
  mutate(for_geocoding = str_c(address, ", Chicago, IL ", zip))

##Geocode apartment addresses and add 'geometry' column
geocoded_apt_data <- tidygeocoder::geocode(clean_apt_data, 
                                  address = for_geocoding, 
                                  method = 'osm', 
                                  lat = latitude ,
                                  long = longitude) %>%
  drop_na(longitude, latitude) %>% 
  st_as_sf(coords = c("longitude", "latitude"), remove = FALSE)

save(geocoded_apt_data, file = 'geocoded_apt_data1129.RData')

#setting CRS for apartment data
st_crs(geocoded_apt_data) <- "+proj=longlat +ellps=WGS84 +datum=WGS84"


#Pipe to add add lat/long geometry to train map
geo_train_map <- train_map %>%
  st_transform("+proj=longlat +ellps=WGS84 +datum=WGS84") %>%
  rowwise() %>%
  mutate(line = str_split(LINES, ",")[[1]][1]) %>%
  mutate(line = as.factor(line)) %>%
  select(line, everything()) %>%
  rowwise() %>%
  mutate(long = geometry[[1]][1], lat = geometry[[1]][2])

#Section to recategorize train lines
oldvals <- as.character(unique(geo_train_map$line))
newvals <- c("Blue", "Green", "Green", "Blue", "Brown", "Brown",
               "Red", "Green", "Green", "Orange", "Red", "Purple",
               "Yellow", "Blue", "Orange", "Pink", "Purple")

lines_recat <- plyr::mapvalues(geo_train_map$line, oldvals, newvals)

clean_train_map <- geo_train_map %>%
  add_column(lines_recat)


#Calculating distance between each train station and each apartment
station_distances <- as_tibble(st_distance(geocoded_apt_data$geometry, clean_train_map$geometry))

add_distance <- function(apartments, stations, ts_distances) {
  
  #initialize outputs (dist to close TS vector and closest TS name vector)
  len <- length(apartments[[1]])
  min_distances <- vector("double", len)
  min_ts_names <-  vector("character", len)
  
  #cycle through indices of apartments
  for (i in seq_along(apartments[[1]])) {
    #extract distance row corresponding to current apt
    row <- slice(ts_distances, i)
    
    #get index of smallest dist
    idx_min <- which.min(row)
    
    #add dist to dist vec
    min_distances[[i]] <- row[[idx_min]]
    
    #add TS name to name vec
    min_ts_names[[i]] <- stations$LONGNAME[[idx_min]]
    
  }
  
  #return apartments with dist and TS name cols added
  final_apts <- as_tibble(apartments) %>%
    add_column(distance_to_train = as_tibble(min_distances),
                           train_station = as_tibble(min_ts_names))
  
  return(final_apts)
  
}

apt_train_dist <- add_distance(geocoded_apt_data, 
                               clean_train_map, 
                               station_distances) %>%
  select(distance_to_train, neighborhood, pp_cost, 
         beds, baths, sqft, train_station, everything() ) %>%
  arrange(pp_cost, distance_to_train, beds) %>%
  filter(distance_to_train < 600)



#Visualize Map with apartments and data, zoomed in
colors <- c("Blue", "Green", "Brown", "Red", "Orange", "Purple", "Yellow", "Pink")


win1 <- c(41.94, -87.73)
win2 <- c(41.88, -87.6)

map <- openmap(win1, win2, type="osm")
map.latlon <- openproj(map, projection = "+proj=longlat +ellps=WGS84 +datum=WGS84")

OpenStreetMap::autoplot.OpenStreetMap(map.latlon)+
  geom_count(apt_train_dist, mapping = aes(longitude, latitude))+
  scale_color_manual(values = colors)



ggplot(data = apt_train_dist)+
  geom_sf(chi_map, mapping = aes())+
  geom_count(mapping = aes(longitude, latitude), size = 0.4, alpha = 0.5)+
  geom_sf(clean_train_map, mapping = aes(color = lines_recat), size = 4.3, alpha=0.7)+
  scale_color_manual(values = colors) +
  coord_sf(
  xlim = c(-87.73, -87.6),
  ylim = c(41.88, 41.94))

#Simple Rent Summary
summary_table <- clean_apt_data %>%
  group_by(neighborhood, beds, baths) %>%
  summarise(n=n(), mean_ppc = mean(pp_cost, na.rm = TRUE), median = median(pp_cost, na.rm = TRUE), mean_sqft = mean(sqft, na.rm = TRUE))
