
"""Test Google's Gemini API through LangChain."""

import os
import sys

from langchain_google_genai import ChatGoogleGenerativeAI


def main():
    """Send a sample query to the Gemini API."""

    # Read the Gemini API key from the environment variable.
    # This keeps the secret key out of the Python source code.
    api_key = os.getenv("GOOGLE_API_KEY")

    # Check whether the API key is available before proceeding.
    # Exit with status code 1 if the key has not been configured.
    if not api_key:
        print("Set GOOGLE_API_KEY before running this script.")
        sys.exit(1)

    # Initialize the Gemini model using LangChain.
    # Temperature 0 encourages more consistent responses.
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0,
    )

    # Define a sample question to test the model.
    our_query = "What is the currency of India?"

    # Send the question to Gemini and store the returned AI message.
    completion = llm.invoke(our_query)

    # Display the text content returned by the model.
    print("Model response:")
    print(completion.content)


# Run main() only when this file is executed directly.
# This allows the function to be imported without running the test.
if __name__ == "__main__":
    main()
