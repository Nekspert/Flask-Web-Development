from flask import Flask, make_response, redirect, abort

app = Flask(__name__)


@app.route('/')
def index():
    response = make_response('<h1>This document carries a cookie!</h1>')
    response.set_cookie('sos', 'NO')
    return response


@app.route('/2')
def index2():
    return '<h1>test</h1>', 302, {'Location': 'http://example.com', 'sos': '213213'}  # redirect


@app.route('/user/<id>')
def get_user(id):
    user = None
    if not user:
        abort(404)
    return '<h1>Hello, {}</h1>'.format(user)


@app.route('/user/<name>')
def user(name):
    return '<h1>Hello {}</h1>'.format(name)


if __name__ == '__main__':
    app.run(debug=True)
