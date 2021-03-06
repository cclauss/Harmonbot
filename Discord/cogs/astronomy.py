
import discord
from discord.ext import commands

import datetime
import dateutil.parser
import inspect
import re

import clients
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Astronomy(bot))

class Astronomy:
	
	def __init__(self, bot):
		self.bot = bot
		# Add specific astronomy subcommands as commands
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and name in ("exoplanet", "iss", "observatory", "telescope"):
				self.bot.add_command(command)
	
	# TODO: random exoplanet, observatory, telescope
	
	@commands.group(aliases = ["space"], invoke_without_command = True)
	@checks.not_forbidden()
	async def astronomy(self, ctx):
		'''exoplanet, iss, observatory, and telescope are also commands as well as subcommands'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@astronomy.command()
	@checks.not_forbidden()
	async def chart(self, ctx, *, chart : str):
		'''WIP'''
		# paginate, https://api.arcsecond.io/findingcharts/HD%205980/
		...
	
	@astronomy.group(aliases = ["archive", "archives"], invoke_without_command = True)
	@checks.not_forbidden()
	async def data(self, ctx):
		'''Data Archives'''
		await ctx.invoke(self.bot.get_command("help"), "astronomy", ctx.invoked_with)
	
	@data.command(name = "eso")
	@checks.not_forbidden()
	async def data_eso(self, ctx, program_id : str):
		'''
		European Southern Observatory
		http://archive.eso.org/wdb/wdb/eso/sched_rep_arc/query
		http://archive.eso.org/wdb/help/eso/schedule.html
		http://archive.eso.org/eso/eso_archive_main.html
		http://telbib.eso.org/
		'''
		async with clients.aiohttp_session.get("https://api.arcsecond.io/archives/ESO/{}/summary/".format(program_id), params = {"format": "json"}) as resp:
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Error: Not Found")
				return
			data = await resp.json()
		# TODO: handle errors
		# TODO: include programme_type?, remarks?, abstract?, observer_name?
		links = []
		if data["abstract_url"]: links.append("[Abstract]({})".format(data["abstract_url"].replace(')', "\)")))
		if data["raw_files_url"]: links.append("[Raw Files]({})".format(data["raw_files_url"].replace(')', "\)")))
		if data["publications_url"]: links.append("[Publications]({})".format(data["publications_url"]))
		fields = []
		if data["period"]: fields.append(("Period", data["period"]))
		if data["observing_mode"] != "(Undefined)": fields.append(("Observing Mode", data["observing_mode"]))
		if data["allocated_time"]: fields.append(("Allocated Time", data["allocated_time"]))
		if data["telescope_name"]: fields.append(("Telescope", data["telescope_name"]))
		if data["instrument_name"]: fields.append(("Instrument", data["instrument_name"]))
		if data["investigators_list"]: fields.append(("Investigators", data["investigators_list"]))
		await ctx.embed_reply('\n'.join(links), title = data["programme_title"] if data["programme_title"] != "(Undefined)" else discord.Embed.Empty, fields = fields)
	
	@data.command(name = "hst")
	@checks.not_forbidden()
	async def data_hst(self, ctx, proposal_id : int):
		'''
		Hubble Space Telescope (HST)
		https://archive.stsci.edu/hst/
		'''
		async with clients.aiohttp_session.get("https://api.arcsecond.io/archives/HST/{}/summary/".format(proposal_id), params = {"format": "json"}) as resp:
			data = await resp.json()
		# TODO: include allocation?, pi_institution?, programme_type_auxiliary?, programme_status?, related_programmes?
		fields = []
		if data["cycle"]: fields.append(("Cycle", data["cycle"]))
		if data["principal_investigator"]: fields.append(("Principal Investigator", data["principal_investigator"]))
		if data["programme_type"] and data["programme_type"] != "(Undefined)": fields.append(("Proposal Type", data["programme_type"]))
		await ctx.embed_reply(data["abstract"], title = data["title"], fields = fields)
	
	@astronomy.command()
	@checks.not_forbidden()
	async def exoplanet(self, ctx, *, exoplanet : str):
		'''Exoplanets'''
		# TODO: list?
		async with clients.aiohttp_session.get("https://api.arcsecond.io/exoplanets/{}".format(exoplanet), params = {"format": "json"}) as resp:
			if resp.status in (404, 500):
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
			'''
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Error: {}".format(data["detail"]))
				return
			'''
		# TODO: include mass?, radius?, bibcodes?, omega_angle?, anomaly angle?, angular_distance?, time_radial_velocity_zero?, hottest_point_longitude?, surface_gravity?, mass_detection_method?, radius_detection_method?
		# TODO: handle one of error_min or error_max, but not other? (SWEEPS-11)
		# TODO: improve efficiency with for loop?
		fields = [("System", data["coordinates"]["system"])]
		if data["coordinates"]["right_ascension"]: fields.append(("Right Ascension", "{}{}".format(data["coordinates"]["right_ascension"], '°' if data["coordinates"]["right_ascension_units"] == "degrees" else ' ' + data["coordinates"]["right_ascension_units"])))
		if data["coordinates"]["declination"]: fields.append(("Right Declination", "{}{}".format(data["coordinates"]["declination"], '°' if data["coordinates"]["declination_units"] == "degrees" else ' ' + data["coordinates"]["declination_units"])))
		# Inclination
		inclination = ""
		if data["inclination"]["value"]: inclination += str(data["inclination"]["value"])
		if data["inclination"]["error_min"] or data["inclination"]["error_max"]:
			if data["inclination"]["error_min"] == data["inclination"]["error_max"]: inclination += '±' + str(data["inclination"]["error_min"])
			else: inclination += "(-{0[error_min]}/+{0[error_max]})".format(data["inclination"])
		if data["inclination"]["value"]: inclination += data["inclination"]["unit"]
		if inclination: fields.append(("Inclination", inclination))
		# Semi-Major Axis
		semi_major_axis = ""
		if data["semi_major_axis"]["value"]: semi_major_axis += str(data["semi_major_axis"]["value"])
		if data["semi_major_axis"]["error_min"] or data["semi_major_axis"]["error_max"]:
			if data["semi_major_axis"]["error_min"] == data["semi_major_axis"]["error_max"]: semi_major_axis += '±' + str(data["semi_major_axis"]["error_min"])
			else: semi_major_axis += "(-{0[error_min]}/+{0[error_max]})".format(data["semi_major_axis"])
		if data["semi_major_axis"]["value"]: semi_major_axis += " AU" if data["semi_major_axis"]["unit"] == "astronomical unit" else ' ' + data["semi_major_axis"]["unit"]
		if semi_major_axis: fields.append(("Semi-Major Axis", semi_major_axis))
		# Orbital Period
		# TODO: include orbital_period error_max + error_min?
		if data["orbital_period"]["value"]: fields.append(("Orbital Period", "{} {}".format(data["orbital_period"]["value"], data["orbital_period"]["unit"])))
		# Eccentricity
		eccentricity = ""
		if data["eccentricity"]["value"]: eccentricity += str(data["eccentricity"]["value"])
		if data["eccentricity"]["error_min"] or data["eccentricity"]["error_max"]:
			if data["eccentricity"]["error_min"] == data["eccentricity"]["error_max"]: eccentricity += '±' + str(data["eccentricity"]["error_min"])
			else: eccentricity += "(-{0[error_min]}/+{0[error_max]})".format(data["eccentricity"])
		if eccentricity: fields.append(("Eccentricity", eccentricity))
		# Lambda Angle
		# Spin-Orbit Misalignment
		# Sky-projected angle between the planetary orbital spin and the stellar rotational spin
		lambda_angle = ""
		if data["lambda_angle"]["value"]: lambda_angle += str(data["lambda_angle"]["value"])
		if data["lambda_angle"]["error_min"] or data["lambda_angle"]["error_max"]:
			if data["lambda_angle"]["error_min"] == data["lambda_angle"]["error_max"]: lambda_angle += '±' + str(data["lambda_angle"]["error_min"])
			else: lambda_angle += "(-{0[error_min]}/+{0[error_max]})".format(data["lambda_angle"])
		if data["lambda_angle"]["value"]: lambda_angle += data["lambda_angle"]["unit"]
		if lambda_angle: fields.append(("Spin-Orbit Misalignment", lambda_angle))
		# Periastron Time
		# https://exoplanetarchive.ipac.caltech.edu/docs/parhelp.html#Obs_Time_Periastron
		time_periastron = ""
		if data["time_periastron"]["value"]: time_periastron += str(data["time_periastron"]["value"])
		if data["time_periastron"]["error_min"] or data["time_periastron"]["error_max"]:
			if data["time_periastron"]["error_min"] == data["time_periastron"]["error_max"]: time_periastron += '±' + str(data["time_periastron"]["error_min"])
			else: time_periastron += "(-{0[error_min]}/+{0[error_max]})".format(data["time_periastron"]) # Necessary?
		if time_periastron: fields.append(("Periastron Time", time_periastron))
		# Conjunction Time
		time_conjonction = ""
		if data["time_conjonction"]["value"]: time_conjonction += str(data["time_conjonction"]["value"])
		if data["time_conjonction"]["error_min"] or data["time_conjonction"]["error_max"]:
			if data["time_conjonction"]["error_min"] == data["time_conjonction"]["error_max"]: time_conjonction += '±' + str(data["time_conjonction"]["error_min"])
			else: time_conjonction += "(-{0[error_min]}/+{0[error_max]})".format(data["time_conjonction"]) # Necessary?
		if time_conjonction: fields.append(("Conjunction Time", time_conjonction))
		# Primary Transit
		# in Julian Days (JD)
		primary_transit = ""
		if data["primary_transit"]["value"]: primary_transit += str(data["primary_transit"]["value"])
		if data["primary_transit"]["error_min"] or data["primary_transit"]["error_max"]:
			if data["primary_transit"]["error_min"] == data["primary_transit"]["error_max"]: primary_transit += '±' + str(data["primary_transit"]["error_min"])
			else: primary_transit += "(-{0[error_min]}/+{0[error_max]})".format(data["primary_transit"]) # Necessary?
		if primary_transit: fields.append(("Primary Transit", primary_transit))
		# Secondary Transit
		# in Julian Days (JD)
		secondary_transit = ""
		if data["secondary_transit"]["value"]: secondary_transit += str(data["secondary_transit"]["value"])
		if data["secondary_transit"]["error_min"] or data["secondary_transit"]["error_max"]:
			if data["secondary_transit"]["error_min"] == data["secondary_transit"]["error_max"]: secondary_transit += '±' + str(data["secondary_transit"]["error_min"])
			else: secondary_transit += "(-{0[error_min]}/+{0[error_max]})".format(data["secondary_transit"])
		if secondary_transit: fields.append(("Secondary Transit", secondary_transit))
		# Impact Parameter
		impact_parameter = ""
		if data["impact_parameter"]["value"]: impact_parameter += str(data["impact_parameter"]["value"])
		if data["impact_parameter"]["error_min"] or data["impact_parameter"]["error_max"]:
			if data["impact_parameter"]["error_min"] == data["impact_parameter"]["error_max"]: impact_parameter += '±' + str(data["impact_parameter"]["error_min"])
			else: impact_parameter += "(-{0[error_min]}/+{0[error_max]})".format(data["impact_parameter"]) # Necessary?
		if data["impact_parameter"]["value"]: impact_parameter += data["impact_parameter"]["unit"]
		if impact_parameter: fields.append(("Impact Parameter", impact_parameter))
		# Radial Velocity Semi-Amplitude
		velocity_semiamplitude = ""
		if data["velocity_semiamplitude"]["value"]: velocity_semiamplitude += str(data["velocity_semiamplitude"]["value"])
		if data["velocity_semiamplitude"]["error_min"] or data["velocity_semiamplitude"]["error_max"]:
			if data["velocity_semiamplitude"]["error_min"] == data["velocity_semiamplitude"]["error_max"]: velocity_semiamplitude += '±' + str(data["velocity_semiamplitude"]["error_min"])
			else: velocity_semiamplitude += "(-{0[error_min]}/+{0[error_max]})".format(data["velocity_semiamplitude"]) # Necessary?
		if data["velocity_semiamplitude"]["value"]: velocity_semiamplitude += ' ' + data["velocity_semiamplitude"]["unit"]
		if velocity_semiamplitude: fields.append(("Radial Velocity Semi-Amplitude", velocity_semiamplitude))
		# Calculated Temperature
		calculated_temperature = ""
		if data["calculated_temperature"]["value"]: calculated_temperature += str(data["calculated_temperature"]["value"])
		if data["calculated_temperature"]["error_min"] or data["calculated_temperature"]["error_max"]:
			if data["calculated_temperature"]["error_min"] == data["calculated_temperature"]["error_max"]: calculated_temperature += '±' + str(data["calculated_temperature"]["error_min"])
			else: calculated_temperature += "(-{0[error_min]}/+{0[error_max]})".format(data["calculated_temperature"]) # Necessary?
		if data["calculated_temperature"]["value"]: calculated_temperature += " K" if data["calculated_temperature"]["unit"] == "Kelvin" else ' ' + data["calculated_temperature"]["unit"]
		if calculated_temperature: fields.append(("Calculated Temperature", calculated_temperature))
		# Measured Temperature
		# TODO: include measured_temperature error_max + error_min?
		if data["measured_temperature"]["value"]: fields.append(("Measured Temperature", "{} {}".format(data["measured_temperature"]["value"], 'K' if data["measured_temperature"]["unit"] == "Kelvin" else data["measured_temperature"]["unit"])))
		# Geometric Albedo
		# TODO: include geometric_albedo error_max + error_min?
		if data["geometric_albedo"]["value"]: fields.append(("Geometric Albedo", data["geometric_albedo"]["value"]))
		# Detection Method
		if data["detection_method"] != "Unknown": fields.append(("Detection Method", data["detection_method"]))
		# Parent Star
		async with clients.aiohttp_session.get(data["parent_star"]) as resp:
			parent_star_data = await resp.json()
		fields.append(("Parent Star", parent_star_data["name"]))
		await ctx.embed_reply(title = data["name"], fields = fields)
	
	@astronomy.command(aliases = ["international_space_station", "internationalspacestation"])
	@checks.not_forbidden()
	async def iss(self, ctx, latitude : float = 0.0, longitude : float = 0.0):
		'''
		Current location of the International Space Station (ISS)
		Enter a latitude and longitude to compute an estimate of the next time the ISS will be overhead
		Overhead is defined as 10° in elevation for the observer at an altitude of 100m
		'''
		if latitude and longitude:
			async with clients.aiohttp_session.get("http://api.open-notify.org/iss-pass.json", params = {"n": 1, "lat": str(latitude), "lon": str(longitude)}) as resp:
				if resp.status == 500:
					await ctx.embed_reply(":no_entry: Error")
					return
				data = await resp.json()
			if data["message"] == "failure":
				await ctx.embed_reply(":no_entry: Error: {}".format(data["reason"]))
				return
			await ctx.embed_reply(fields = (("Duration", utilities.secs_to_letter_format(data["response"][0]["duration"])),), footer_text = "Rise Time", timestamp = datetime.datetime.utcfromtimestamp(data["response"][0]["risetime"]))
		else:
			async with clients.aiohttp_session.get("http://api.open-notify.org/iss-now.json") as resp:
				data = await resp.json()
			latitude = data["iss_position"]["latitude"]
			longitude = data["iss_position"]["longitude"]
			map_icon = "http://i.imgur.com/KPfeEcc.png" # 64x64 satellite emoji png
			map_url = "https://maps.googleapis.com/maps/api/staticmap"
			map_url += "?center={0},{1}&zoom=3&size=640x640&maptype=hybrid&markers=icon:{2}|anchor:center|{0},{1}".format(latitude, longitude, map_icon)
			await ctx.embed_reply("[:satellite_orbital: ]({})".format(map_url), fields = (("Latitude", latitude), ("Longitude", longitude)), image_url = map_url, timestamp = datetime.datetime.utcfromtimestamp(data["timestamp"]))
	
	@astronomy.command()
	@checks.not_forbidden()
	async def object(self, ctx, *, object : str):
		'''WIP'''
		# https://api.arcsecond.io/objects/alpha%20centurai/
		...
	
	@astronomy.command()
	@checks.not_forbidden()
	async def observatory(self, ctx, *, observatory : str):
		'''
		Observatories
		Observing sites on Earth
		'''
		# TODO: list?
		async with clients.aiohttp_session.get("https://api.arcsecond.io/observingsites/", params = {"format": "json"}) as resp:
			data = await resp.json()
		for _observatory in data:
			if observatory.lower() in _observatory["name"].lower():
				fields = [("Latitude", _observatory["coordinates"]["latitude"]), ("Longitude", _observatory["coordinates"]["longitude"]), ("Height", "{}m".format(_observatory["coordinates"]["height"])), ("Continent", _observatory["address"]["continent"]), ("Country", _observatory["address"]["country"])]
				time_zone = "{0[time_zone_name]}\n({0[time_zone]})".format(_observatory["address"])
				if len(time_zone) <= 22: time_zone = time_zone.replace('\n', ' ') # 22: embed field value limit without offset
				fields.append(("Time Zone", time_zone))
				if _observatory["IAUCode"]: fields.append(("IAU Code", _observatory["IAUCode"]))
				telescopes = []
				for telescope in _observatory["telescopes"]:
					async with clients.aiohttp_session.get(telescope) as resp:
						telescope_data = await resp.json()
					telescopes.append(telescope_data["name"])
				if telescopes: fields.append(("Telescopes", '\n'.join(telescopes)))
				await ctx.embed_reply(title = _observatory["name"], title_url = _observatory["homepage_url"] or discord.Embed.Empty, fields = fields)
				return
		await ctx.embed_reply(":no_entry: Observatory not found")
	
	@astronomy.command()
	@checks.not_forbidden()
	async def people(self, ctx):
		'''Current people in space'''
		# TODO: add input/search option
		async with clients.aiohttp_session.get("http://api.open-notify.org/astros.json") as resp:
			data = await resp.json()
		await ctx.embed_reply('\n'.join("{0[name]} ({0[craft]})".format(person) for person in data["people"]), title = "Current People In Space ({})".format(data["number"]))
	
	@astronomy.command()
	@checks.not_forbidden()
	async def publication(self, ctx, *, bibcode : str):
		'''Publications'''
		async with clients.aiohttp_session.get("https://api.arcsecond.io/publications/{}/".format(bibcode), params = {"format": "json"}) as resp:
			data = await resp.json()
		if not data:
			await ctx.embed_reply(":no_entry: Publication not found")
			return
		if isinstance(data, list): data = data[0]
		await ctx.embed_reply(title = data["title"], fields = (("Journal", data["journal"]), ("Year", data["year"]), ("Authors", data["authors"])))
	
	@astronomy.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def telegram(self, ctx):
		'''Quick publications, often related to ongoing events occuring in the sky'''
		await ctx.invoke(self.bot.get_command("help"), "astronomy", ctx.invoked_with)
	
	@telegram.command(name = "atel", aliases = ["astronomerstelegram"])
	@checks.not_forbidden()
	async def telegram_atel(self, ctx, number : int):
		'''
		The Astronomer's Telegram
		http://www.astronomerstelegram.org/
		'''
		# TODO: use textwrap
		async with clients.aiohttp_session.get("https://api.arcsecond.io/telegrams/ATel/{}/".format(number), params = {"format": "json"}) as resp:
			if resp.status == 500:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		# TODO: include credential_certification?, authors?, referring_telegrams?, external_links?
		description = data["content"].replace('\n', ' ')
		if len(description) > 1000: description = description[:1000] + "..."
		fields = []
		if len(data["subjects"]) > 1 or data["subjects"][0] != "Undefined": fields.append(("Subjects", ", ".join(sorted(data["subjects"]))))
		related = ["[{0}](http://www.astronomerstelegram.org/?read={0})".format(related_telegram) for related_telegram in sorted(data["related_telegrams"])]
		if related:
			for i in range(0, len(related), 18):
				fields.append(("Related Telegrams", ", ".join(related[i: i + 18])))
		if data["detected_objects"]: fields.append(("Detected Objects", ", ".join(sorted(data["detected_objects"]))))
		await ctx.embed_reply(description, title = data["title"], title_url = "http://www.astronomerstelegram.org/?read={}".format(number), fields = fields)
	
	@telegram.command(name = "gcn", aliases = ["circulars"])
	@checks.not_forbidden()
	async def telegram_gcn(self, ctx, number : str):
		'''
		GCN Circulars
		https://gcn.gsfc.nasa.gov/
		'''
		# TODO: use textwrap
		async with clients.aiohttp_session.get("https://api.arcsecond.io/telegrams/GCN/Circulars/{}/".format(number), params = {"format": "json"}) as resp:
			if resp.status in (404, 500):
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		# TODO: include submitter?, authors?, related_circulars?, external_links?
		description = re.sub("([^\n])\n([^\n])", r"\1 \2", data["content"])
		description = re.sub("\n\s*\n", '\n', description)
		if len(description) > 1000: description = description[:1000] + "..."
		description = clients.code_block.format(description)
		await ctx.embed_reply(description, title = data["title"] or discord.Embed.Empty, title_url = "https://gcn.gsfc.nasa.gov/gcn3/{}.gcn3".format(number), timestamp = dateutil.parser.parse(data["date"]) if data["date"] else discord.Embed.Empty)
	
	@astronomy.command(aliases = ["instrument"])
	@checks.not_forbidden()
	async def telescope(self, ctx, *, telescope : str):
		'''
		Telescopes and instruments
		At observing sites on Earth
		'''
		# TODO: list?
		async with clients.aiohttp_session.get("https://api.arcsecond.io/telescopes/", params = {"format": "json"}) as resp:
			data = await resp.json()
		for _telescope in data:
			if telescope.lower() in _telescope["name"].lower():
				async with clients.aiohttp_session.get(_telescope["observing_site"]) as resp:
					observatory_data = await resp.json()
				fields = [("Observatory", "[{0[name]}]({0[homepage_url]})".format(observatory_data) if observatory_data["homepage_url"] else observatory_data["name"])]
				if _telescope["mounting"] != "Unknown": fields.append(("Mounting", _telescope["mounting"]))
				if _telescope["optical_design"] != "Unknown": fields.append(("Optical Design", _telescope["optical_design"]))
				properties = []
				if _telescope["has_active_optics"]: properties.append("Active Optics")
				if _telescope["has_adaptative_optics"]: properties.append("Adaptative Optics")
				if _telescope["has_laser_guide_star"]: properties.append("Laser Guide Star")
				if properties: fields.append(("Properties", '\n'.join(properties)))
				await ctx.embed_reply(title = _telescope["name"], fields = fields)
				return
		await ctx.embed_reply(":no_entry: Telescope/Instrument not found")

