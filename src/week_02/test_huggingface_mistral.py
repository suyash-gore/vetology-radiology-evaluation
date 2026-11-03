
"""Test a Mistral model through Hugging Face and LangChain."""

import os
import sys

from langchain_huggingface import HuggingFaceEndpoint


def main():
    """Send a sample query to the Hugging Face model."""

    # Read the Hugging Face API token from an environment variable.
    # This avoids storing the secret token directly in the source code.
    api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

    # Check whether the token is configured before making an API request.
    # Exit with status code 1 if the token is missing.
    if not api_token:
        print("Set HUGGINGFACEHUB_API_TOKEN before running this script.")
        sys.exit(1)

    # Initialize the Mistral model through Hugging Face's hosted inference.
    # max_new_tokens limits the maximum number of generated tokens.
    llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.3",
        huggingfacehub_api_token=api_token,
        max_new_tokens=100,
    )

    # Define a sample question to test the model's response.
    our_query = "What is the currency of India?"

    # Send the question to the model and store the generated text.
    completion = llm.invoke(our_query)

    # Print the generated response to the terminal.
    # HuggingFaceEndpoint.invoke() returns text rather than an AI message.
    print("Model response:")
    print(completion)


# Execute main() only when this script is run directly.
if __name__ == "__main__":
    main()
