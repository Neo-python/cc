from flask import Flask
from flask_apscheduler import APScheduler


class Config(object):

    JOBS = [
        {
            'id': 'backup',
            'func': 'mytiming:backup',
            'args': None,
            'trigger': {
                'type': 'interval',
                'seconds': 1,
                'max_instances': 1
            },
        }
    ]
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)


@app.route("/")
def hello():
    return "hello world"


def backup():
    print('backup')


if __name__ == '__main__':
    scheduler = APScheduler()
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.start()
    app.run()