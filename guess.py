"""Project 1: Number Guessing Game
Run: python guess.py
"""
import random

MAX_ATTEMPTS = 7


def ask_guess():
    """Keep asking until the user enters a whole number between 1 and 100."""
    while True:
        text = input("Your guess (1-100): ").strip()
        if not text.isdigit():
            print("Please enter a whole number.")
            continue
        number = int(text)
        if 1 <= number <= 100:
            return number
        print("Number must be between 1 and 100.")


def play_round():
    secret = random.randint(1, 100)
    attempts = 0
    print(f"\nI'm thinking of a number between 1 and 100. You have {MAX_ATTEMPTS} tries.")

    while attempts < MAX_ATTEMPTS:
        guess = ask_guess()
        attempts += 1

        if guess < secret:
            print(f"Too low! ({MAX_ATTEMPTS - attempts} left)")
        elif guess > secret:
            print(f"Too high! ({MAX_ATTEMPTS - attempts} left)")
        else:
            print(f"Correct! You got it in {attempts} tries.")
            break
    else:
        print(f"You lost! The number was {secret}.")


def main():
    while True:
        play_round()
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
