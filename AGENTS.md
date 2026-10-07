# CS4300 coursework

Personal course repository at `ripleyforge-chase/cs4300`; unrelated to Ripley Forge production.
Preserve completed homework in its own directory. Do not submit to Canvas.

| Capability | Owner | Callers / validation |
| --- | --- | --- |
| Movie, seat, booking data and reservation rules | `homework2/movie_theater_booking/bookings/models.py`, `services.py` | API serializers and HTML views; `bookings/tests.py` |
| REST API | `bookings/api.py`, `serializers.py` | DRF router; API tests and Behave |
| Browser experience | `bookings/views.py`, `forms.py`, `templates/`, `static/` | Django URLs; HTML tests and Behave |
| Demo data | `bookings/management/commands/seed_demo.py` | Local setup and Render startup; command tests |

Paths in the last three rows are relative to `homework2/movie_theater_booking`.
Run instructions and test commands live in `homework2/README.md`.
Use a feature branch and pull request. Commit and push meaningful milestones.
