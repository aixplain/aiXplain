from aixplain.v2.resource import BaseResource


class Script(BaseResource):
    @classmethod
    def upload(cls, script_path: str) -> "Script":
        """Upload a script to the server.

        Args:
            script_path: str: The path to the script.

        Returns:
            Script: The script.
        """
        from aixplain.factories.script_factory import ScriptFactory

        file_id, metadata = ScriptFactory.upload_script(script_path)

        return ScriptFactory.upload_script({"fileId": file_id, "metadata": metadata})
