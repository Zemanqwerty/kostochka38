from django import forms

from captcha.fields import CaptchaField


class CommentForm(forms.Form):
    author = forms.CharField(max_length=100)
    captcha = CaptchaField()
    body = forms.CharField(widget=forms.Textarea)
    
    def clean_author(self):
        author = self.cleaned_data['author']
        num_words = len(author.strip())
        if int(num_words) < 3:
            raise forms.ValidationError(u"Слишком короткое имя. Минимум 3 символа.")
        return author
        
    def clean_body(self):
        body = self.cleaned_data['body']
        num_words = len(body.strip())
        if int(num_words) < 2:
            raise forms.ValidationError(u"Слишком короткое сообщение. Минимум 2 символа.")
        return body
