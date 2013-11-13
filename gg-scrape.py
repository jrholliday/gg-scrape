import dateutil.parser
import os
import re
import urllib

# http://code.google.com/p/webscraping/
import webscraping.webkit

def gg_scrape(group, verbose=False):
    group_url = 'https://groups.google.com/forum/#!forum/{0}'
    topic_url = 'https://groups.google.com/forum/#!topic/{0}/{1}'
    raw_url   = 'https://groups.google.com/forum/message/raw?msg={0}/{1}/{2}'

    ajax_pause = 1
    archive_dir = "./{0}/".format(group)

    w = webscraping.webkit.WebkitBrowser()

    # Create the archive directory
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    # Get a list of all the topics
    w.get(group_url.format(group))
    w.wait(ajax_pause)

    html = w.page().mainFrame().toHtml()
    counts = re.findall('([0-9]*) of ([0-9]*) topics', html)
    n,N = map(int, (counts + [('0','0')])[0])

    if verbose: print "{0} topics in this group...".format(N)

    # Scroll to bottom of div to force ajax loading
    while (n<N):
        w.js('''a=document.getElementsByTagName("div");
                for(i in a){o=a[i];o.scrollTop=o.scrollHeight;}''')
        w.wait(ajax_pause)

        # Have we got them all yet?
        html = w.page().mainFrame().toHtml()
        counts = re.findall('([0-9]*) of ([0-9]*) topics', html)
        n,N = map(int, (counts + [('0','0')])[0])

    topics = re.findall('id="topic_row_(.*?)"', html)
    assert (len(topics) == N)

    if verbose: print "{0} topics loaded!".format(len(topics))

    # Loop over each topic
    for i, topic in enumerate(topics):
        # load webpage
        w.get(topic_url.format(group, topic))

        # wait for the ajax to load
        w.wait(ajax_pause)
        html = w.page().mainFrame().toHtml()
        N = int(re.findall('([0-9]*) posts? by [0-9]* authors?', html)[0])

        # Grab all the individual posts in the thread
        posts = re.findall('id="b_action_(.*?)"', html)
        assert (len(posts) == N)

        if verbose: print "{0} ({1}) -".format(i+1,N),

        for j, post in enumerate(posts):
            # Grab the email data
            url = raw_url.format(group, topic, post)
            email = urllib.urlopen(url).read()

            # Parse out the send date
            email_date = re.findall('Date: (.*)', email)[0]
            date = dateutil.parser.parse(email_date)

            # Save the file with the timestamp as it's title
            name = archive_dir + date.isoformat() + ".txt"
            with open(name, "w") as datafile:
                datafile.write(email)

            if verbose: print j+1,
        if verbose: print ""

    # That's all, folks.
    return None


def make_mbox(archive_dir):
    name = (archive_dir+'/').replace('//','/').split('/')[-2]
    with open(name+'.mbox', 'w') as mbox:
        for infile in sorted(glob.glob(archive_dir+'/*.txt')):
            email_data = open(infile).read()
            # Parse the sender and date
            email_from = re.findall('From: .* <(.*)>', email_data)[0]
            email_date = re.findall('Date: (.*)', email_data)[0]
            # (re)Format the date
            date = dateutil.parser.parse(email_date).strftime("%c")
            # Append the data to our mbox
            mbox.write("From {0}  {1}\n".format(email_from, date))
            mbox.write(email_data)
            mbox.write("\n")
    return None


if __name__ == "__main__":
    import sys
    # Read group name from stdin
    group = sys.argv[1]
    # Go go gadget scraper...
    gg_scrape(group, True)
    make_mbox(group)
