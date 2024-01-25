

def read_user_from_file(filename):
    """
        Reads user information from a file.

        Params:
        - filename (str): The name of the file containing user information.

        Returns:
        - dict or None: A dictionary containing user information (including 'name' and 'client_id') if successful,
          or None if an error occurs or the file is not found.
        """

    try:
        with open(filename, "r") as file:
            lines = file.readlines()

            # Extracting information
            name = lines[0].strip()
            client_id = lines[1].strip()

            client = {
                'name': name, 'client_id': client_id
            }
            return client

    except FileNotFoundError:
        print(f"Info: File '{filename}' not found.")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

    return None
