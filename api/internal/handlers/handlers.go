package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/ru6ich/go-notes-platform/api/internal/models"
)

type Handler struct {
	DB *pgxpool.Pool
}

func New(db *pgxpool.Pool) *Handler {
	return &Handler{DB: db}
}

func (h *Handler) Register(mux *http.ServeMux) {
	mux.HandleFunc("/healthz", h.healthz)
	mux.HandleFunc("/notes", h.notes)
}

func (h *Handler) healthz(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{
		"status": "ok",
	})
}

func (h *Handler) notes(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.listNotes(w, r)
	case http.MethodPost:
		h.createNote(w, r)
	default:
		w.Header().Set("Allow", "GET, POST")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func (h *Handler) createNote(w http.ResponseWriter, r *http.Request) {
	var req models.CreateNoteRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid json body", http.StatusBadRequest)
		return
	}

	req.Text = strings.TrimSpace(req.Text)
	if req.Text == "" {
		http.Error(w, "text is required", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	var note models.Note
	err := h.DB.QueryRow(
		ctx,
		`INSERT INTO notes (text) VALUES ($1) RETURNING id, text, created_at`,
		req.Text,
	).Scan(&note.ID, &note.Text, &note.CreatedAt)
	if err != nil {
		http.Error(w, "failed to insert note", http.StatusInternalServerError)
		return
	}

	writeJSON(w, http.StatusCreated, note)
}

func (h *Handler) listNotes(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	rows, err := h.DB.Query(
		ctx,
		`SELECT id, text, created_at FROM notes ORDER BY created_at DESC LIMIT 100`,
	)
	if err != nil {
		http.Error(w, "failed to query notes", http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	notes := make([]models.Note, 0)

	for rows.Next() {
		var note models.Note
		if err := rows.Scan(&note.ID, &note.Text, &note.CreatedAt); err != nil {
			http.Error(w, "failed to scan notes", http.StatusInternalServerError)
			return
		}
		notes = append(notes, note)
	}

	if err := rows.Err(); err != nil {
		http.Error(w, "rows error", http.StatusInternalServerError)
		return
	}

	writeJSON(w, http.StatusOK, notes)
}

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(data)
}
