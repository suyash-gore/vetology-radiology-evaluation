
"""Test an OpenAI GPT model through LangChain."""

import os
import sys

from langchain_openai import ChatOpenAI


def main():
    """Send a sample query to the OpenAI API."""

    # Read the OpenAI API key from an environment variable.
    # This keeps the secret key out of the Python source code.
    api_key = os.getenv("OPENAI_API_KEY")

    # Check whether the API key is configured before making a request.
    # Exit with status code 1 if the key is missing.
    if not api_key:
        print("Set OPENAI_API_KEY before running this script.")
        sys.exit(1)

    # Initialize the GPT model using LangChain's ChatOpenAI integration.
    # The API key is passed explicitly to authenticate the request.
    llm = ChatOpenAI(
        model="gpt-4",
        api_key=api_key,
    )

    # Define a sample question to test the API integration.
    our_query = "What is the currency of India?"

    # Send the question to OpenAI and store the returned AI message.
    completion = llm.invoke(our_query)

    # Print the text content of the model's response.
    print("Model response:")
    print(completion.content)


# Run main() only when this file is executed directly.
if __name__ == "__main__":
    main()
