from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
import os, json
from app.irsystem.models.database_helpers import get_donations, get_tweets_by_politician, get_votes_by_politician
from empath import Empath

project_name = "Fundy"
net_id = "Samantha Dimmer: sed87; James Cramer: jcc393; Dan Stoyell: dms524; Isabel Siergiej: is278; Joe McAllister: jlm493"

def filter_donations(donations, politician, issue):
	issue = issue.lower()
	relevant_fields = [
		"DonorCommitteeNameNormalized",
		"DonorOccupationNormalized",
		"DonorEmployerNormalized",
		"DonorNameNormalized",
		"DonorCandidateOffice",
		"DonorOrganization",
	]

	filtered = []
	for don in donations:
		is_relevant = False
		for field in relevant_fields:
			if issue in don[field].lower():
				is_relevant = True
		if is_relevant:
			filtered.append(don)

	return filtered

def process_donations(donations):
	total = 0
	for don in donations:
		total += float(don["TransactionAmount"])

	return {
		"total": total,
		"sample": sorted(donations, key=lambda d:d["TransactionAmount"], reverse=True)[:10]
	}

@irsystem.route('/', methods=['GET'])
def search():
	politician_query = request.args.get('politician_name')
	free_form_query = request.args.get('free_form')
	lexicon = Empath()
	data = None
	if not politician_query or not free_form_query: # no input
		output_message = 'Please provide an input'
		return render_template('search.html', 
				name=project_name, 
				netid=net_id, 
				output_message=output_message, 
				data=data,
		)
	else:
		output_message = "Politician Name: " + politician_query
		data = {
			"politician": politician_query,
			"issue": free_form_query,
			"donations": [],
			"tweets": [],
			"votes": [],
		}
		if politician_query:
			#Get empath categories for free form query
			if free_form_query:
				issues_categories = lexicon.analyze(free_form_query, normalize=True)
			raw_donation_data = get_donations(politician_query)
			if(raw_donation_data.count() > 0):
				# filtered_donations = filter_donations(raw_donation_data, politician_query, free_form_query)
				# don_data = process_donations(filtered_donations)
				don_data = {
					"total": 10,
					"sample": [],
				}
				data["donations"] = don_data
			raw_tweet_data = get_tweets_by_politician(politician_query)
			if(raw_tweet_data.count() > 0):
				data["tweets"].append(raw_tweet_data.next()["tweet_text"])
			raw_vote_data = get_votes_by_politician(politician_query)
			for vote in raw_vote_data:
				vote_categories = lexicon.analyze(vote["vote"]["description"], normalize=True)
				intersect = False
				#Determine if query and vote have similar topics
				for category in vote_categories:
					if vote_categories[category] > 0 and issues_categories[category] > 0:
						intersect = True
					#If query and vote have similar topics, add the vote to vote data
					if intersect:
						description = vote["vote"]["description"]
						politician_vote = "Unknown"
						for position in vote["vote"]["positions"]:
							if position["PoliticianName"] == politician_query:
								politician_vote = position["vote_position"]
								break
						data["votes"].append({"description":description, "vote_position":politician_vote})
		if free_form_query:
			print("Need to implement this")
		return render_template('search.html', 
				name=project_name, 
				netid=net_id, 
				output_message=output_message, 
				data=data,
		)
