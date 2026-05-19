CREATE USER 'grafana' @'%' IDENTIFIED BY 'grafana1';
GRANT SELECT ON WeatherStations.* TO grafana;