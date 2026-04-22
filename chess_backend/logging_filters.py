class ExcludeProfessionalTimerAccessFilter:
    """
    Hide high-frequency professional timer polling access logs from terminal output.
    """

    def filter(self, record):
        message = record.getMessage()
        return "/professional-timer/" not in message

