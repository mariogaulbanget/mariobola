# MARIOBOLA — Portal final untuk Cloudflare Pages + GitHub

## Struktur

```text
index.html
data/
  jadwal-harian.txt       <- update pertandingan setiap hari
  live-links.json         <- link LIVE per pertandingan
  content.json            <- streaming, gallery, event, sosial, link utama/alternatif
assets/
  logo-mariobola.png      <- LOGO MARIOBOLA TETAP
  teams/                  <- logo tim, berdasarkan slug nama tim
  streaming/              <- gambar channel live
  gallery/                <- gambar kemenangan
  events/                 <- gambar event
```

## Update jadwal
Edit `data/jadwal-harian.txt`. Format: heading liga, lalu baris `DD/MM HH:MM HOME VS AWAY HANDICAP`. Jangan ubah `index.html`.

## Logo tim otomatis
Untuk `Deportivo La Coruna`, upload logo ke `assets/teams/deportivo-la-coruna.png`. Untuk `Elche`: `assets/teams/elche.png`. Sistem membuat nama file dari nama tim. Jika logo belum ada, kartu menampilkan fallback 2 huruf dan tidak rusak.

## Link LIVE per pertandingan
Edit `data/live-links.json`. Kunci harus berbentuk `YYYY-MM-DD|HH:MM|slug-home|slug-away`. Contoh: `2026-08-18|02:00|deportivo-la-coruna|elche`.

## Streaming, Gallery, Event, Social, Link utama
Edit `data/content.json`. Gambar gunakan path lokal seperti `assets/gallery/kemenangan-01.jpg`. Upload file gambar tersebut ke folder yang sesuai di GitHub.

## Deploy
Commit perubahan di GitHub. Cloudflare Pages yang terhubung ke repository akan melakukan deploy otomatis. Setelah deploy, gunakan Ctrl+F5.

## Penting
Logo MARIOBOLA utama menggunakan `assets/logo-mariobola.png` dan tidak bergantung pada URL gambar eksternal.
