from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField,TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validateUsername(self, username):
        user = db.execute("SELECT * FROM users WHERE username = :username",{
            "username": username.data
        }).fetchone()
        if user:
            raise ValidationError('Username Taken!')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    
    submit = SubmitField('Login')

class ReviewForm(FlaskForm):
    rating = SelectField("Add your Rating", choices=[(1, '1 - Poor'),(2, '2 - Fair'),(3, '3 - Good'),(4, '4 - Very Good'),(5, '5 - Excellent')], default=1)
    content = TextAreaField("Comment", render_kw={"rows": 10, "cols": 30}, validators=[DataRequired(), Length(min= 2, max=200)])
    submit = SubmitField("Rate")

class ProfileForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(),
        Length(min=3,max=20)
    ])
    email = StringField("Email", validators=[
        Email()
    ])
    submit = SubmitField("Submit")

    def validateUsername(self, username):
        user = db.execute("SELECT * FROM users WHERE username = :username",{
            "username": username.data
        }).fetchone()
        if user:
            raise ValidationError('Username Taken!')