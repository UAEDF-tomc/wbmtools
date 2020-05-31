<html>
<head>
<title>
<?php 
  if(basename(__FILE__)=="index.php"){
    $user = get_current_user(); 
    echo str_replace('/eos/user/'.$user[0].'/'.$user.'/www','',getcwd());
  } else {
    // TITLE -- inserted by makeWebpage.py
  }
?>
</title>

<!-- Styles to be used -->
<style type='text/css'>
body {
    font-family: "Helvetica", sans-serif;
    font-size: 9pt;
    line-height: 10.5pt;
}
h1 {
    font-size: 14pt;
    margin: 0.5em 1em 0.2em 1em;
    text-align: left;
    display: inline-block;
}
div.fixed {
    position: fixed;
    white-space: nowrap;
    width:100%;
}
div.bar {
    display: inline-block;
    margin: 0.5em 0.6em 0.2em 0.6em;
    padding: 10px;
    color: #29407C;
    background: white;
    text-align: center;
    border: 1px solid #29407C;
    border-radius: 5px;
}
div.barEmpty {
    color: #ccc;
    border: 1px solid #ccc;
}
a.bar {
    display: inline-block;
    margin: 0.5em 0.6em 0.2em 0.6em;
    padding: 10px;
    color: white;
    background: #29407C;
    text-align: center;
    border: 1px solid #29407C;
    border-radius: 5px;
}
a.bar:hover {
    background-color: #4CAF50;
    color: white;
}
div.list {
    font-size: 13pt;
    margin: 0.5em 1em 1.2em 1em;
    display: block; 
    clear: both;
}
div.list li {
    margin-top: 0.3em;
}
div.list2 li {
    margin-top: 0.3em;
    line-height: 1.3;
}
a { text-decoration: none; color: #29407C; }
a:hover { text-decoration: underline; color: #D08504; }
</style>
</head>

<body>

<!-- Adding some buttons on top -->
<div class="fixed">
<?php
  // If "path" exists, show a button to "path" with text "name"
  function showIfExists($path, $name){
    if(file_exists($path)){
      if(__FILE__!=$path){
        $user = get_current_user();
        $webPath = str_replace('eos/user/'.$user[0].'/'.$user.'/www', $user, $path);
        $webPath = str_replace('index.php', '', $webPath);
        if(!empty($_SERVER['QUERY_STRING'])) $webPath = $webPath.'/?'.$_SERVER['QUERY_STRING'];
        print "<span><a class=\"bar\" href=\"$webPath\">$name</a></span>";
      } else {
        print "<span><div class=\"bar\">$name</div></span>";
      }
    } else {
      print "<span><div class=\"bar barEmpty\">$name</div></span>";
    }
  }
  if(basename(__FILE__)!="lowestSeeds.php"){     // lowestSeed.php is a special case
    showIfExists('..', 'parent');
  }

  $fullPath=__FILE__;

  // Search if one of the entries in $years appear in the path and put it in "myYear" and the full dir in which it appears in "myYearDir"
  $years=array('2016','2017','2018');
  $myYear=NULL;
  foreach($years as $y){
    foreach(explode('/', $fullPath) as $subdir){
      if(strpos($subdir, $y)===0){
        $myYearDir='/'.$subdir.'/';
        $temp=explode('-',$subdir);
        $myYear=$temp[0];
      }
    }
  }

  // Try to substitute "old" with "new" in the "yearDir" part and returns the new path if it exists
  function tryModifier($yearDir, $old, $new, $fullPath){
    $newYearDir=str_replace($old, $new, $yearDir);
    $newPath   =str_replace($yearDir, $newYearDir, $fullPath);
    if(file_exists(rtrim($newPath,"/"))) return $newPath;
    else                                 return NULL;
  }

  // Try to modify "old" in "new" in "yearDir", if old is NULL try to see if new can be appended in the directory
  function modifyYear($yearDir, $old, $new, $fullPath){
    if(!is_null($old)) return tryModifier($yearDir, $old, $new, $fullPath);
    if(strpos($yearDir, $new)!==false) return $fullPath;
    $tryAtEnd=tryModifier($yearDir, $yearDir, substr($yearDir, 0, -1).'-'.$new.'/', $fullPath);
    if(!is_null($tryAtEnd)) return $tryAtEnd;
    foreach(explode('-',$yearDir) as $sub){
      $tryInBetween=tryModifier($yearDir, $sub, $sub.'-'.$new, $fullPath);
      if(!is_null($tryInBetween)) return $tryInBetween;
    }
    return NULL;
  }

  // If myYear is not null, try modifiers and put buttons for it
  if(!is_null($myYear)){
    $path2016 = modifyYear($myYearDir, $myYear, '2016', $fullPath);
    $path2017 = modifyYear($myYearDir, $myYear, '2017', $fullPath);
    $path2018 = modifyYear($myYearDir, $myYear, '2018', $fullPath);

    function multipleOptions($options){
      $counter = 0;
      foreach($options as $o){
        if(file_exists($o)){
          $counter +=1;
        }
      }
      return ($counter > 1);
    }

    if(multipleOptions(array($path2016,$path2017,$path2018))){
      showIfExists($path2016, '2016');
      showIfExists($path2017, '2017');
      showIfExists($path2018, '2018');
    }
  }

  if(basename(__FILE__)=="index.php"){     // index.php has a filter to search through the triggers
    print '<span><h1><form>filter  <input type="text" name="match" size="25" value="';
    if (isset($_GET['match'])) print htmlspecialchars($_GET['match']);
    print '" /><input type="Submit" value="Go" /></form></h1></span>';
  }
?>
</div>
<br style="clear:both" />

<?php
  // if it is an index.php make a list of available subdirectories or triggers -->
  if(basename(__FILE__)=="index.php"){
    print '<div class="list" style="margin-top: 2cm">';
    print '<ul>';
    $triggers = array();
    foreach (glob("*") as $filename){
      if($filename == "index.php") continue;
      if(isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
      if(is_dir($filename) and $filename != 'json'){
        print "<li>[DIR] <a href=\"$filename\">$filename</a></li>";
      } else if (pathinfo($filename, PATHINFO_EXTENSION) == 'php' and $filename != "index.php"){
        $displayname = pathinfo($filename, PATHINFO_FILENAME);
        array_push($triggers,"<li><a href=\"$filename\">$displayname</a></li>");
      }
    }
    foreach ($triggers as $file){print $file;}
    print '</ul>';
    print '</div>';
  }
?>
<br style="clear:both;margin-bottom:4mm" />
<!-- DIV       - inserted by makeWebpage.py -->
<!-- LISTSEEDS - inserted by makeWebpage.py -->
</body>
</html>
