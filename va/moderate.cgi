#!/usr/bin/perl -Tw

####################################333
# Election application
# Written by J�rgen Elgaard Larsen
# HTML and design by Ole Tange
# Licensed under the GNU GPL version 3.



use CGI;
use DBI;
use HTML::Entities;

my %admins = (
	      1234 => 1,
	      );



my $q = new CGI;

# Read and clean template
my $template = $q->param('template') || '';
$template =~ s/[^a-zA-Z0-9]//g;

# Default template
unless ($template){
    $template='skabelon';
}

# Get template
my $skab = '<html><head><!--HEADER--></head><body><!--CONTENT--></body></html>';
if (open SKAB, "<${template}.html"){
    $skab = join "", <SKAB>;
    close SKAB;
}

my $page = '';
my $header = '';

my $uid = int $q->param('uid');

my $isadmin = $admins{$uid} || 0;

if ($isadmin){

    my $qid = int $q->param('qid');

    my $dbh = DBI->connect('dbi:mysql:host=localhost;database=valg', 'valg', 'secret', {});
    
    unless ($dbh){
	$page .= qq|<p class="error">No database connection</p>|;
    }

    ## Save changes
    if ($q->param('save')){
	
	$dbh->do("UPDATE question SET edited = ? WHERE id = ?", undef, $q->param('moderated'), $qid);

	$dbh->do("DELETE FROM votes WHERE question = ? AND uid = ?", undef, $qid, $uid);
	$dbh->do("INSERT INTO votes (question, uid, vote) VALUES (?,?,?)", undef, $qid, $uid, $q->param('point_adjust'));
	
	$page .= qq|<p class="good">�ndringer gemt</p>|;

    }


    ## Find question
    my $sth = $dbh->prepare(" select *, votes.vote as mine from
                             ( select id, content, edited, sum(vote) as total
                                  from question left outer join votes on 
                                  (votes.question = question.id)
                                where question.id = ?   
                                group by question.id, content, edited
                             ) as q
                              left outer join votes on (votes.uid = ?
                              and votes.question = q.id)
                              order by total desc, q.id asc");

    if ($sth){
	$sth->execute($qid,$uid);

	my $row = $sth->fetchrow_hashref;

	unless ($row){
	    $page .= qq|<p class="error">SQL error: $DBI::errstr</p>|;
	}

	
	my $content = encode_entities($row->{edited} || $row->{content} || '');
	my $mine = int ($row->{mine} || 0);


	## Show form
    
	$page .= qq|
	    <form action="moderate.cgi" method="post">
	    <input type="hidden" name="qid" value="$qid" />
	    <input type="hidden" name="template" value="${template}" />
	    <input type="hidden" name="uid" value="${uid}" />

	    <h2>Moder�r sp�rgsm�l:</h2>
	    <textarea cols="60" rows="7" name="moderated">$content</textarea>
	    <br/>

	    Pointjustering: <input type="text" name="point_adjust" value="${mine}" /><br/>
	<input type="submit" name="save" value="OK" />
	</form>

	<p class="origquestion"><b>Original question:</b><br>$row->{content}</p>
	|;

	$sth->finish;
    } else {
	$page .= qq|<p class="error">SQL error: $DBI::errstr</p>|;
    }

} else {
    $page .= qq|<p class="error">Du er ikke administrator. Fy!</p>|;
}


$page .= qq|<p><a href="javascript:window.close()" class="close">Luk vinduet</a></p>|;




print "Content-Type: text/html\n\n";

$skab =~ s/<!--HEADER-->/$header/g;
$skab =~ s/<!--CONTENT-->/$page/g;

print $skab;



exit;

