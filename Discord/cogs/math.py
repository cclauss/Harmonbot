
import discord
from discord.ext import commands

import asyncio
import concurrent.futures
import math
import multiprocessing
import sympy

from clients import py_code_block
from utilities import checks

def setup(bot):
	bot.add_cog(Math())

class Math:
	
	'''
	Also see Matrix category
	'''
	
	def __local_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	# Basic
	
	@commands.command()
	async def add(self, ctx, *numbers : float):
		'''Add numbers together'''
		if not numbers:
			await ctx.embed_reply("Add what?")
			return
		await ctx.embed_reply("{} = {:g}".format(" + ".join("{:g}".format(number) for number in numbers), sum(numbers)))
	
	@commands.command(aliases = ["calc", "calculator"])
	async def calculate(self, ctx, *, equation : str):
		'''Calculator'''
		#_equation = re.sub("[^[0-9]+-/*^%\.]", "", equation).replace('^', "**") #words
		replacements = {"pi" : "math.pi", 'e' : "math.e", "sin" : "math.sin", "cos" : "math.cos", "tan" : "math.tan", '^' : "**"}
		allowed = set("0123456789.+-*/^%()")
		for key, value in replacements.items():
			equation = equation.replace(key, value)
		# TODO: use filter
		equation = "".join(character for character in equation if character in allowed)
		print("Calculated " + equation)
		with multiprocessing.Pool(1) as pool:
			async_result = pool.apply_async(eval, (equation,))
			future = ctx.bot.loop.run_in_executor(None, async_result.get, 10.0)
			try:
				result = await asyncio.wait_for(future, 10.0, loop = ctx.bot.loop)
				await ctx.embed_reply("{} = {}".format(equation, result))
			except discord.errors.HTTPException:
				await ctx.embed_reply(":no_entry: Output too long")
			except SyntaxError:
				await ctx.embed_reply(":no_entry: Syntax error")
			except ZeroDivisionError:
				await ctx.embed_reply(":no_entry: Error: Division by zero")
			except (concurrent.futures.TimeoutError, multiprocessing.context.TimeoutError):
				await ctx.embed_reply(":no_entry: Execution exceeded time limit")
	
	@commands.command()
	async def exp(self, ctx, value : float):
		'''
		Exponential function
		e ** value | e ^ value
		'''
		try:
			await ctx.embed_reply(math.exp(value))
		except OverflowError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@commands.command()
	async def factorial(self, ctx, value : int):
		'''Factorial'''
		try:
			await ctx.embed_reply(math.factorial(value))
		except OverflowError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@commands.command(aliases = ["greatest_common_divisor"])
	async def gcd(self, ctx, value_a : int, value_b : int):
		'''Greatest common divisor'''
		await ctx.embed_reply(math.gcd(value_a, value_b))
	
	@commands.command(aliases = ["squareroot", "square_root"])
	async def sqrt(self, ctx, value : float):
		'''Square root'''
		await ctx.embed_reply(math.sqrt(value))
	
	# Calculus
	
	@commands.command(aliases = ["differ", "derivative", "differentiation"])
	async def differentiate(self, ctx, *, equation : str):
		'''
		Differentiate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await ctx.embed_reply("`{}`".format(sympy.diff(equation.strip('`'), x)), title = "Derivative of {}".format(equation))
		except Exception as e:
			await ctx.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@commands.group(aliases = ["integral", "integration"], invoke_without_command = True)
	async def integrate(self, ctx, *, equation : str):
		'''
		Integrate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await ctx.embed_reply("`{}`".format(sympy.integrate(equation.strip('`'), x)), title = "Integral of {}".format(equation))
		except Exception as e:
			await ctx.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@integrate.command(name = "definite")
	async def integrate_definite(self, ctx, lower_limit : str, upper_limit : str, *, equation : str):
		'''
		Definite integral of an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await ctx.embed_reply("`{}`".format(sympy.integrate(equation.strip('`'), (x, lower_limit, upper_limit))), title = "Definite Integral of {} from {} to {}".format(equation, lower_limit, upper_limit))
		except Exception as e:
			await ctx.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	# Trigonometry
	# TODO: a(sin/cos/tan)h aliases
	
	@commands.command(alises = ["acosine", "arccos", "arccosine", "a_cosine", "arc_cos", "arc_cosine"])
	async def acos(self, ctx, value : float):
		'''Arc cosine function'''
		await ctx.embed_reply(math.acos(value))
	
	@commands.command(alises = ["acosineh", "arccosh", "arccosineh", "a_cosineh", "arc_cosh", "arc_cosineh"])
	async def acosh(self, ctx, value : float):
		'''Inverse hyperbolic cosine function'''
		await ctx.embed_reply(math.acosh(value))
	
	@commands.command(alises = ["asine", "arcsin", "arcsine", "a_sine", "arc_sin", "arc_sine"])
	async def asin(self, ctx, value : float):
		'''Arc sine function'''
		await ctx.embed_reply(math.asin(value))
	
	@commands.command(alises = ["asineh", "arcsinh", "arcsineh", "a_sineh", "arc_sinh", "arc_sineh"])
	async def asinh(self, ctx, value : float):
		'''Inverse hyperbolic sine function'''
		await ctx.embed_reply(math.asinh(value))
	
	# TODO: atan2
	@commands.command(alises = ["atangent", "arctan", "arctangent", "a_tangent", "arc_tan", "arc_tangent"])
	async def atan(self, ctx, value : float):
		'''Arc tangent function'''
		await ctx.embed_reply(math.atan(value))
	
	@commands.command(alises = ["atangenth", "arctanh", "arctangenth", "a_tangenth", "arc_tanh", "arc_tangenth"])
	async def atanh(self, ctx, value : float):
		'''Inverse hyperbolic tangent function'''
		await ctx.embed_reply(math.atanh(value))
	
	@commands.command(alises = ["cosine"])
	async def cos(self, ctx, value : float):
		'''Cosine function'''
		await ctx.embed_reply(math.cos(value))
	
	@commands.command(alises = ["cosineh"])
	async def cosh(self, ctx, value : float):
		'''Hyperbolic cosine function'''
		await ctx.embed_reply(math.cosh(value))
	
	@commands.command(alises = ["sine"])
	async def sin(self, ctx, value : float):
		'''Sine function'''
		await ctx.embed_reply(math.sin(value))
	
	@commands.command(alises = ["sineh"])
	async def sinh(self, ctx, value : float):
		'''Hyperbolic sine function'''
		await ctx.embed_reply(math.sinh(value))
	
	@commands.command(alises = ["tangent"])
	async def tan(self, ctx, value : float):
		'''Tangent function'''
		await ctx.embed_reply(math.tan(value))
	
	@commands.command(alises = ["tangenth"])
	async def tanh(self, ctx, value : float):
		'''Hyperbolic tangent function'''
		await ctx.embed_reply(math.tanh(value))
