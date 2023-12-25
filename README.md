# Youtube subscriptions summarizer

## Components
### Web
`python manage.py runserver`

### RQ workers for AI tasks
`python manage.py rqworker ai`

### RQ workers for not-high-load tasks
`python manage.py rqworker default`

### RQ scheduler
`python manage.py rqscheduler`

### Telegram bot
`python manage.py run_bot`
