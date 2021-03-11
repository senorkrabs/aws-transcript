
""" /*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal in the Software
 * without restriction, including without limitation the rights to use, copy, modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 * PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */ """

import sys, os
import json
import datetime
import logging
import pandas as pd
import csv
from stat import S_ISDIR, S_ISREG
import glob
import argparse
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)



def main():
	arg_parser = argparse.ArgumentParser(
		description="Parses transcription JSON documents produced by AWS Transcribe and generates timestamped CSV, TSV, and HTML files with speaker/channel labels and confidence scores.", 
		epilog="NOTES: The script expects the JSON document to be from AWS Transcribe. It extracts the first transcription from each item. Other alternatives are ignored. Rows are separated by speaker/channel changes. If the transcription doesn't contain speakers/channels then rows are separated by punctuation."
	)
	arg_parser.add_argument('--path', type=str, required=True, nargs='+', help="The path containing the transcription files. Supports glob pattern matching.")
	arg_parser.add_argument('--results-dir', type=str, required=False, default="./results", help="The directory where the results will be written. Defaults to the ./results/")
	arg_parser.add_argument('--csv', action='store_true', required=False, default=False, help="Generate a CSV for each transcription. If no options specified, CSV will be generated.")
	arg_parser.add_argument('--tsv', action='store_true', required=False, default=False, help="Generate a TSV for each file.")
	arg_parser.add_argument('--html', action='store_true', required=False, default=False, help="Generate a HTML for each file.")

	args = vars(arg_parser.parse_args())
	
	path = args["path"]
	results_dir = args["results_dir"]	
	generate_csv = args["csv"]
	generate_tsv = args["tsv"]
	generate_html = args["html"]

	if not (generate_csv or generate_tsv or generate_html):
		generate_csv = True

	assert os.path.isdir(results_dir)

	process_files(path, results_dir, generate_csv, generate_tsv, generate_html)

def process_files(path, results_dir, generate_csv, generate_tsv, generate_html):
	log.debug ("Path: {}".format(path))
	files = []
	for item in path:
		files.extend(glob.glob(item))
	log.info("Number of files to process: {}".format(len(files)))
	for f in files:
		convert_transcription(f, results_dir, generate_csv, generate_tsv, generate_html)

def convert_transcription(filename, results_dir, generate_csv, generate_tsv, generate_html):
	log.info ("Processing file: {}".format(filename))
		
	try: 

		data = json.load(open(filename, "r", encoding="utf-8"))
		assert "jobName" in data
		assert "results" in data
		assert data.get("status", "") == "COMPLETED"

		if "speaker_labels" in data["results"].keys():
			log.info ("Found speaker labels")
			transcription = process_speaker_labels(data)
		elif "channel_labels" in data["results"].keys():
			log.info ("Found channel labels")
			transcription = process_channel_labels(data)
		else:
			log.info ("Transcription doesn't contain speakers or labels")
			transcription = process_plain(data)
		log.info("Sorting records")
		transcription.sort_values(by='start_time', inplace=True)

		results_file = results_dir+'/'+os.path.split(filename)[1]
		if generate_csv:
			log.info ("Writing {}".format(results_file+'.csv'))
			transcription.to_csv(results_file+'.csv', index=False )
		if generate_tsv:
			transcription.drop(columns='average_confidence').to_csv(results_file+'.tsv', sep='\t', header=False, quoting=csv.QUOTE_NONE, index=False)
			log.info ("Writing {}".format(results_file+'.tsv'))
		if generate_html:
			transcription.to_html(results_file+'.html', index=False)
			log.info ("Writing {}".format(results_file+'.html'))
	except Exception as ex:
		log.exception(ex)

def process_plain(data):
	transcription = pd.DataFrame(
		columns={			
			'start_time': pd.Series([], dtype='float'), 
			'average_confidence':pd.Series([], dtype='float'), 
			'transcription': pd.Series([], dtype='str') 
		}
	)	

	confidences=[]
	line=''
	time=0

	for item in data['results']['items']:
		content = item['alternatives'][0]['content']
		if 'redactions' in item['alternatives'][0]:
			confidence = item['alternatives'][0]['redactions'][0]['confidence']
		else:
			confidence = item['alternatives'][0]['confidence']

		if item.get('type', '') == 'pronunciation':
			if time is None:
				time=item['start_time']
			
			line = content if line == '' else line+' '+content
			confidences.append(float(confidence))
		elif item.get('type', '') == 'punctuation':
			line = line+content
			transcription = transcription.append(
					{
						'start_time': float(time),
						'average_confidence': round(sum(confidences)/len(confidences), 4),
						'transcription': line
					},
					ignore_index=True
			)		
			line=''
			time=None
			confidences = []					
		else:
			log.warning('Unexpected type "{}" in item: {}'.format(item.get('type', ''), item))
			
	transcription = transcription.append(
		{
			'start_time': float(time),
			'average_confidence': round(sum(confidences)/len(confidences), 4),
			'transcription': line
		},
		ignore_index=True

	)

	return(transcription)

def process_channel_labels(data):
	transcription = pd.DataFrame(
		columns={
			'channel': pd.Series([], dtype='str'), 
			'start_time': pd.Series([], dtype='float'), 
			'average_confidence':pd.Series([], dtype='float'), 
			'transcription': pd.Series([], dtype='str') 
		}
	)	
	log.info('Channels: {}'.format(data['results'].get('channel_labels', {}).get('number_of_channels',None)))
	
	channel_item_times={}
	for channel in data['results'].get('channel_labels', {}).get('channels', {}):
		log.info("Indexing channel: {}".format(channel['channel_label']))
		if len(channel["items"]) > 0:
			for item in channel['items']:			
				if item.get('start_time', None):
					channel_item_times[item['start_time']] = channel['channel_label']



	confidences=[]
	line=''
	time=0
	current_channel=None

	for item in data['results']['items']:
		content = item['alternatives'][0]['content']
		if 'redactions' in item['alternatives'][0]:
			confidence = item['alternatives'][0]['redactions'][0]['confidence']
		else:
			confidence = item['alternatives'][0]['confidence']
		item_channel=channel_item_times.get(item.get('start_time', ''), current_channel)
		if current_channel is None:
			current_channel = item_channel
		if item_channel != current_channel:
			log.debug('Channel changed to {} at {}'.format(item_channel, item['start_time']))
			transcription = transcription.append(
					{
						'channel': current_channel,
						'start_time': float(time),
						'average_confidence': round(sum(confidences)/len(confidences), 4),
						'transcription': line
					},
					ignore_index=True
			)			
			line=''
			current_channel=item_channel
			time=item['start_time']
			confidences = []
		if item.get('type', '') == 'pronunciation':
			line = content if line == '' else line+' '+content
			confidences.append(float(confidence))
		elif item.get('type', '') == 'punctuation':
			line = line+content
		else:
			log.warning('Unexpected type "{}" in item: {}'.format(item.get('type', ''), item))
			
	transcription = transcription.append(
		{
			'channel': current_channel,
			'start_time': float(time),
			'average_confidence': round(sum(confidences)/len(confidences), 4),
			'transcription': line
		},
		ignore_index=True

	)

	return(transcription)



def process_speaker_labels(data):

	transcription = pd.DataFrame(
		columns={
			'speaker': pd.Series([], dtype='str'), 
			'start_time': pd.Series([], dtype='float'), 
			'average_confidence':pd.Series([], dtype='float'), 
			'transcription': pd.Series([], dtype='str') 
		}
	)	

	log.info('Speakers: {}'.format(data['results'].get('speaker_labels', {}).get('speakers',None)))
	log.info('Segments: {}'.format(len(data['results'].get('speaker_labels', {}).get('segments', {}))))
	speaker_start_times={}
	log.info("Indexing speaker times.")
	for segment in data['results'].get('speaker_labels', {}).get('segments', {}):
		if len(segment["items"]) > 0:
			for item in segment['items']:			
				speaker_start_times[item['start_time']] = item['speaker_label']

	confidences=[]
	line=''
	time=0
	current_speaker=None

	for item in data['results']['items']:
		content = item['alternatives'][0]['content']
		if 'redactions' in item['alternatives'][0]:
			confidence = item['alternatives'][0]['redactions'][0]['confidence']
		else:
			confidence = item['alternatives'][0]['confidence']
		item_speaker=speaker_start_times.get(item.get('start_time', ''), current_speaker)
		if current_speaker is None:
			current_speaker = item_speaker
		if item_speaker != current_speaker:
			log.debug('Speaker changed to {} at {}'.format(item_speaker, item['start_time']))
			transcription = transcription.append(
					{
						'speaker': current_speaker,
						'start_time': float(time),
						'average_confidence': round(sum(confidences)/len(confidences), 4),
						'transcription': line
					},
					ignore_index=True
			)			
			line=''
			current_speaker=item_speaker
			time=item['start_time']
			confidences = []
		if item.get('type', '') == 'pronunciation':
			line = content if line == '' else line+' '+content
			confidences.append(float(confidence))
		elif item.get('type', '') == 'punctuation':
			line = line+content
		else:
			log.warning('Unexpected type "{}" in item: {}'.format(item.get('type', ''), item))
			
	transcription = transcription.append(
		{
			'speaker': current_speaker,
			'start_time': float(time),
			'average_confidence': round(sum(confidences)/len(confidences), 4),
			'transcription': line
		},
		ignore_index=True

	)

	return transcription

main()

