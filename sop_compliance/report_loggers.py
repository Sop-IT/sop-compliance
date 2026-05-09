
from extras.choices import LogLevelChoices
from extras.scripts import Script
from extras.validators import CustomValidator

#
# Reports logging
#

class AbstractCheckResultLogger():
    def log(self, cr):
        raise NotImplementedError("The class must define a log(cr) method.")

class CheckResult():
    def __init__(self, level, site, text, field:str|None=None):
        self.level=level
        self.site=site
        self.text=text
        self.field=field
    def is_failure(self)->bool:
        return (LogLevelChoices.LOG_FAILURE==self.level)
    def is_warning(self)->bool:
        return (LogLevelChoices.LOG_WARNING==self.level)
    def is_info(self)->bool:
        return (LogLevelChoices.LOG_INFO==self.level)
    def is_success(self)->bool:
        return (LogLevelChoices.LOG_SUCCESS==self.level)

class DebugPrintCheckResultLogger(AbstractCheckResultLogger):
    def __init__(self):
        pass
    def log(self, cr:CheckResult):
       print(f"Debug logger  :  {cr.level} - {cr.site} - {cr.text} ")

class ReportCheckResultLogger(AbstractCheckResultLogger):
    logger:Script
    def __init__(self, logger:Script):
        self.logger=logger
    def log(self, cr:CheckResult):
        if cr.level==LogLevelChoices.LOG_FAILURE:
            self.logger.log_failure(cr.text, cr.site)
        elif cr.level==LogLevelChoices.LOG_WARNING:
            self.logger.log_warning(cr.text, cr.site)
        elif cr.level==LogLevelChoices.LOG_SUCCESS:
            self.logger.log_success(cr.text, cr.site)
        elif cr.level==LogLevelChoices.LOG_INFO:
            self.logger.log_info(cr.text, cr.site)
        else:
            self.logger.log_debug(cr.text, cr.site)

class ValidatorCheckResultLogger(AbstractCheckResultLogger):
    logger:CustomValidator
    def __init__(self, logger:CustomValidator, failprefix:str):
        self.logger=logger
        self.failprefix=failprefix
    def log(self, cr:CheckResult):
        if cr.level==LogLevelChoices.LOG_FAILURE:
            self.logger.fail(self.failprefix + cr.text, cr.field)
            
class CheckResultList():
    lst:list[CheckResult]
    def __init__(self):
        self.lst=[]
    def append(self, cr:CheckResult):
        if cr is not None:
            self.lst.append(cr)
    def dump_to(self, logger:AbstractCheckResultLogger):
        for cr in self.lst:
            logger.log(cr)
    def has_failure(self)->bool:
        for cr in self.lst:
            if cr.is_failure():
                return True
        return False
    def has_warning(self)->bool:
        for cr in self.lst:
            if cr.is_warning():
                return True
        return False



