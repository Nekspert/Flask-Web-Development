from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms.fields import StringField, SubmitField


class NameForm(FlaskForm):
    name = StringField(label='What is your name?', validators=[DataRequired()])
    submit = SubmitField(label='Submit')
