from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql
import json
from flask_mail import Mail
import os,math
from werkzeug.utils import secure_filename
pymysql.install_as_MySQLdb()

__all__=[secure_filename]
local_server=True
with open('config.json', 'r')as c:
    params=json.load(c)["params"]
app=Flask(__name__)
app.secret_key = 'super-key'
app.config['UPLOADER_FOLDER']=params['location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_username'],
    MAIL_PASSWORD=params['gmail_pass']
)
mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db=SQLAlchemy(app)
class Contact(db.Model):
    """ sno , name , Email , phone_num date make a class of your table attribute"""
    sno = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    Email = db.Column(db.String(20),nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    date = db.Column(db.String(20),nullable=True)
    msg = db.Column(db.String(80), nullable=False)
class Posts(db.Model):
    """ sno , name , Email , phone_num date make a class of your table attribute"""
    sno = db.Column(db.Integer,primary_key=True)
    Title = db.Column(db.String(80),nullable=False)
    sub_heading = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(20),nullable=False)
    content = db.Column(db.String(120),nullable=False)
    posted_by = db.Column(db.String(20), nullable=True)
    img_file = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20),nullable=True)
@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_post']))
    # [0:params['no_of_post']]
    # posts=posts[]
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_post']):(page-1)*int(params['no_of_post'])+int(params['no_of_post'])]
    if page==1:
        prev="#"
        next="/?page="+ str(page+1)
    elif page==last:
        prev="/?page=" + str(page-1)
        next="#"
    else:
        prev="/?page=" + str(page-1)
        next = "/?page=" + str(page + 1)
    # pagination logic
    # First
    # prev=#
    # next=page+1
    # midle page
    # prev =  page - 1
    # next = page + 1
    # Last page
    # prev =  page-1
    # next = #



    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)
@app.route("/index")
def home1():
    posts = Posts.query.filter_by().all()[0:params['no_of_post']]
    return render_template('index.html', params=params, posts=posts)
@app.route("/about")
def about():
    return render_template('about.html',params=params)
@app.route("/contact",methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        """ taking the data rom form in contact page"""

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        """ here we have to match the colomumn of the table with this variable above by calling the class """
        entry =Contact(name=name,phone_num=phone,msg=message,Email=email,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from' + name,
                          sender=email,
                          recipients=[params['gmail_username']],
                          body=message + "\n" + phone)

    return render_template('contact.html',params=params)
@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return  render_template('post.html',params=params,post=post)
@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user']==params['admin_username']):
        if request.method == 'POST':
            box_title=request.form.get('heading')
            box_tline=request.form.get('tline')
            box_slug=request.form.get('slug')
            box_img_file = request.form.get('img_file')
            box_content=request.form.get('content')
            box_posted_by = "Admin"
            date=datetime.now()

            if sno =='0':
                post=Posts(Title=box_title,sub_heading=box_tline,slug=box_slug,content=box_content,posted_by=box_posted_by,img_file=box_img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.Titile=box_title
                post.sub_heading=box_tline
                post.slug=box_slug
                post.content=box_content
                post.img_file=box_img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+ sno)
        post=Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)
@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
   if('user' in session and session['user']==params['admin_username']):
       posts = Posts.query.all()
       return render_template('dashboard.html',params=params,posts=posts)

   if (request.method=='POST'):
       username=request.form.get('uname')
       password=request.form.get('pass')
       if username==params['admin_username'] and password==params['admin_pass']:
           session['user']=username
           posts=Posts.query.all()
           return render_template('dashboard.html',params=params,posts=posts)
   return render_template('signin.html', params=params)
@app.route("/uploader",methods = ['GET','POST'])
def uploader():
   if ('user' in session and session['user'] == params['admin_username']):
       if(request.method=='POST'):
           f=request.files['file1']
           f.save(os.path.join(app.config['UPLOADER_FOLDER']),secure_filename(f.filename))
           return "Upload Succesfully"
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')
@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_username']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')
app.run(debug=True)