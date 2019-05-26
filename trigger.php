<?php

$LOG_FILE = dirname(__FILE__).'/hook.log';
$SECRET_KEY = 'ms1234';

$body = file_get_contents("php://input");
$header = getallheaders();
$hmac = hash_hmac('sha1', $body, $SECRET_KEY);
if ( isset($header['X-Hub-Signature']) && $header['X-Hub-Signature'] === 'sha1='.$hmac ) {
	$payload = json_decode($HTTP_RAW_POST_DATA, true);
	exec('git pull');
	file_put_contents($LOG_FILE, date("[Y-m-d H:i:s]")." ".$_SERVER['REMOTE_ADDR']." git pulled: ".$payload['after']." ".$payload['commits'][0]['message']."\n", FILE_APPEND|LOCK_EX);
} else {
	file_put_contents($LOG_FILE, date("[Y-m-d H:i:s]")." invalid access: ".$_SERVER['REMOTE_ADDR']."\n", FILE_APPEND|LOCK_EX);
}