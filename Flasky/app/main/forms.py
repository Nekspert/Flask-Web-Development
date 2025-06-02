from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_pagedown.fields import PageDownField


class NameForm(FlaskForm):
    name = StringField(label='What is your name?', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


class PostForm(FlaskForm):
    body = PageDownField("What's in your mind", validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('Submit')