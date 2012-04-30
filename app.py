import datetime
import os
import re
import subprocess as sub
import time

from flask import Flask, render_template, render_template_string, url_for
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html',
            articles = _get_items('articles', render="article_preview.html"),
            notepads = _get_items('notepads', render="notepad_preview.html"))

@app.route('/notes/')
def notes():
    #base = '/static/notepads/%s/' % filename # TODO: Helper, for sake of RSS

    notes = _get_items('notepads', render="notepad_single.html")
    return render_template('notes.html', notes=notes)


@app.route('/articles/<filename>/')
def article(filename):
    # TODO We should be getting slug from the URL, not like this.
    slug = re.search('(\d{4})-(\d{2})-(\d{2})-(.*)', filename).group(4)
    base = '/static/articles/%s/' % filename # TODO: Helper, for sake of RSS
    return _content(('articles', filename), template="article_full.html", slug=slug, base=base)


@app.route('/notes/<filename>/')
def note(filename):
    # TODO We should be getting slug from the URL, not like this.
    slug = re.search('(\d{4})-(\d{2})-(\d{2})-(.*)', filename).group(4)
    base = '/static/notepads/%s/' % filename # TODO: Helper, for sake of RSS
    return _content(('notepads', filename), template="notepad_full.html", slug=slug, base=base)


def _get_items(folder, render=False):
    return_list = []
    rendered = False

    for f in os.listdir('static/%s' % folder):
        d = re.search('(\d{4})-(\d{2})-(\d{2})-(.*)', f)

        if d:
            date = datetime.datetime(int(d.group(1)), int(d.group(2)), int(d.group(3)))
            slug = d.group(4)
            date_sort = time.mktime(date.timetuple())

            if render:
                rendered = _content((folder, f), template=render, slug=slug, filename=f)

            return_list.append({'date':date, 'slug':slug, 'filename':f,
                'folder': folder, 'rendered': rendered})


    return_list.sort(reverse=True, key=lambda d: time.mktime(d['date'].timetuple()))
    return return_list

def _content(get_template, **context):
    if isinstance(get_template, tuple):
        get_template = '%s/%s/content.html' % get_template

    with open('static/%s' % get_template, 'r') as f:
        return render_template_string(f.read(), **context)

# TODO: Clean this up!
# TODO: Move out of here
def _less():
    all_css = []

    # Get bootstrap top file
    with open('static/css/bootstrap/top.less', 'r') as css:
        all_css.append(css.read())

    # Get main CSS
    for f in os.listdir('static/css/'):
        if re.search('(.*).less', f):
            with open('static/css/%s' % (f), 'r') as css:
                all_css.append(css.read())

    # Get articles CSS
    for c in _get_items('articles'):
        with open('static/%s/%s/style.less' % (c['folder'], c['filename']), 'r') as f:
            base = '@base:"/static/articles/%s/";' % c['filename'] # TODO: Helper, for sake of RSS
            output = '#%s-%s {\n%s\n%s }' % (c['folder'], c['slug'], base, f.read())
            all_css.append(output)

    # Get bootstrap bottom file
    with open('static/css/bootstrap/bottom.less', 'r') as css:
        all_css.append(css.read())

    all_css_out = '\n'.join(all_css)
    with open('static/css/output/style-all.less', 'w') as f:
        f.write(all_css_out)

    p = sub.Popen('lessc static/css/output/style-all.less > static/css/output/style.css',
                  shell=True,stdout=sub.PIPE,stderr=sub.PIPE)
    # Using this since we want it to block (debug only!)
    o, e = p.communicate()

if __name__ == '__main__':
    app.debug = True

    # Compile LESS first
    if app.debug:
        app.before_request(_less)

    app.run()
