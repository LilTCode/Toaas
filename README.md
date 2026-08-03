# TO-AAS (Technology-Oriented Academic Advisory System)

A web-based intelligent academic advisory platform for Computer Science undergraduate programmes at Abiola Ajimobi Technical University (AA-TU), Ibadan.

## Architecture

- Backend: Django + Django REST Framework
- Frontend: React + Tailwind CSS
- Database: MySQL
- Authentication: JWT, OTP-based registration, role-based access control
- Modules: Accounts, Course Management, Advisory Engine, AI Chatbot

## Initial setup

1. Create a Python virtual environment in `backend`.
2. Install dependencies from `backend/requirements.txt`.
3. Configure `.env` with database credentials and secret keys.
4. Run Django migrations and create a superuser.
5. Install frontend dependencies in `frontend` and start the Vite app.

## Notes

This scaffold includes the initial data model for courses, cognitive demand profiles, transcripts, student cognitive profiles, and advisory recommendations.
