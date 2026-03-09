package models

import "time"

type Note struct {
	ID        int64     `json:"id"`
	Text      string    `json:"text"`
	CreatedAt time.Time `json:"created_at"`
}

type CreateNoteRequest struct {
	Text string `json:"text"`
}
