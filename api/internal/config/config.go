package config

import (
	"fmt"
	"os"
)

type Config struct {
	AppPort     string
	DatabaseURL string
}

func Load() (*Config, error) {
	appPort := getEnv("APP_PORT", "8080")
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbName := getEnv("DB_NAME", "notesdb")
	dbUser := getEnv("DB_USER", "notesuser")
	dbPassword := getEnv("DB_PASSWORD", "notessecret")

	databaseURL := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		dbUser, dbPassword, dbHost, dbPort, dbName,
	)

	return &Config{
		AppPort:     appPort,
		DatabaseURL: databaseURL,
	}, nil
}

func getEnv(key, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}
