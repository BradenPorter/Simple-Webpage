import os
import jinja2
import webapp2
from google.appengine.ext import ndb
#Below is an alternative escape/markup module that works better in my opinion 
from markupsafe import Markup, escape 


template_dir = os.path.join(os.path.dirname(__file__), "templates")

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

#Below we create and populate a list of my notes by opening and reading them one by one
current_stage=5
count=0
safe=Markup("<br>")#we Markup the html that we don't want escaped
#notes' index will correspond to the stage
notes=[None]*(current_stage+1) #with +1 we don't get a list assignment index range error
while count<current_stage:
	count+=1
	stage="Stage"+str(count)+"_Notes"
	with open (stage) as myfile:
		notes[count]=myfile.read()
		notes[count]=escape(notes[count])
		notes[count]=notes[count].replace('\n', safe)#we replace \n with the safe <br>
del notes[0]#gets rid of the first item in notes which is empty

#Below we create a wall for comments and then construct a wall_key for our datastor (taken from wallbook.py)
DEFAULT_WALL = 'Public'
def wall_key(wall_name = DEFAULT_WALL):
  return ndb.Key('Wall', wall_name)

#Below we create a class Comment which contains a username, text, and date
class Comment(ndb.Model):
	username = ndb.StringProperty(indexed=False)
	text = ndb.StringProperty(indexed=False)
	date = ndb.DateTimeProperty(auto_now_add = True)

#Below is the request handler taken from the Udacity example
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        t=jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

#Below is the class which gets the comments and renders the webpage with the notes and comments
class MainPage(Handler):
  def get(self):
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL
    comments_query = Comment.query(ancestor = wall_key(wall_name)).order(-Comment.date)#the '-' reverses the order
    comments = comments_query.fetch()
    self.render("Webpage.html", notes=notes, comments=comments)

class ErrorPage(Handler):
  def get(self):
    self.render("error.html")

#Below is the class which gets the content of the comment and posts then redirects to the main page after escaping it
class Post(webapp2.RequestHandler):
        def post(self):
			wall_name = self.request.get('wall_name',DEFAULT_WALL)
			comment = Comment(parent = wall_key(wall_name))
			comment.username = escape(self.request.get('username'))
			comment.text = escape(self.request.get('text')).strip()#removes trailing characters like spaces
			if comment.text=='':
				self.redirect('/error')
			else:
				comment.put()
				self.redirect('/')

app = webapp2.WSGIApplication([("/", MainPage),("/comments", Post),("/error", ErrorPage)], debug=True)