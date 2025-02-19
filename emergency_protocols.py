def emergency(issue, location, details):
	print(f"Emergency! {issue} at {location}! {details}")

	if issue.lower() == "fire":
		return "Fire Department"
	elif issue.lower() == "break-in":
		return "Police Department"
	elif issue.lower() == "injury":
		return "Medical Unit"
	elif issue.lower() == "medical":
		return "Medical Unit"
	elif issue.lower() == "theft":
		return "Police Department"
	elif issue.lower() == "school shooting":
		return "Religious Prayer"
	else:
		return "School Administration"