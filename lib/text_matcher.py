import re
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class TextMatcher:
    def __init__(self, text):
        self.text = text

    def match(self, text = None, textMatches=None, textContains=None):
        # log.info(f"match text: {self.text}, text={text}, textMatches={textMatches}, textContains={textContains}")
        if textMatches:
            result = re.match(textMatches, self.text)
            # log.info(f"result {result}")
            return result
        if textContains:
            result = textContains in self.text
            # log.info(f"result {result}")
            return result
        if text:
            result = self.text == text
            # log.info(f"result {result}")
            return result
        # log.info("return False")
        return False

if __name__ == "__main__":
    matcher = TextMatcher("看指定视频得金币")
    assert matcher.match(text="看指定视频得金币")
    assert matcher.match(textMatches=r"^看指定视频得金币$")
    assert matcher.match(textContains="看指定视频得金币")
    assert not matcher.match(text="看指定视频得金币1")
    assert not matcher.match(textMatches=r"^看指定视频得金币1$")
    assert not matcher.match(textContains="看指定视频得金币1")
