# Tadpole Interactive Story Engine
<sub>Version 1.0.0-Alpha</sub>

A web-based visual novel engine that enables non-programmers to design and publish branching, choice-driven interactive stories through a graphical interface.

For CSE 0613-308 | Software Development Management Lab

# Tech Stack

- Python
- Django
- SQLite

# Features

- **Story Flow**: See a story unfold with branching paths based on user choices.


# Get Started

- Clone the repository:
  ```bash
  git clone https://github.com/fardinkamal62/tadpole-interactive-story-engine.git
  ```

- Navigate to the project directory:
  ```bash
  cd tadpole-interactive-story-engine
  ```
  
- Create a virtual environment:
  ```bash
  python -m venv venv
  ```

- Activate the virtual environment:
  - On Windows:
    ```bash
    venv\Scripts\activate
    ```
  - On macOS/Linux:
    ```bash
    source venv/bin/activate
    ```
  
- Install the required dependencies:
  ```bash
  pip install -r requirements.txt
  ```

- Apply database migrations:
  ```bash
  python manage.py migrate
  ```
  
- Create a superuser to access the admin panel:
  ```bash
  python manage.py createsuperuser
  ```

- Start the development server:
  ```bash
  python manage.py runserver
  ```



### Made with ❤️ by team Tadpole

- [Fardin Kamal](https://github.com/fardinkamal62) - Architecture, deployment, integration, System Design
- [Maheer Alam](https://github.com/MaheerJishan3/) - React, UI/UX, visual editor
- [MD. Siamul Islam Shoaib](https://github.com/mdsiamulislam) - Django, API