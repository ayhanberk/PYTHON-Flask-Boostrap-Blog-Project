# Flask-Boostrap-Blog-Project
# Python ve Flask ile Blog projeme hoş geldiniz.
## Bu Proje Kendimi Geliştirmek Amaçlı Yapılmıştır.

projede kullanıcıya bilgi vermek için kullanılan message.html dosyası
```html
{% with messages = get_flashed_messages(with_categories=true) %}
 {% if messages %}

  {% for category, message in messages %}
   <div class="alert alert-{{category}}" role="alert">
   {{message}} 
   </div>
   {% endfor %}

 {% endif %}
{% endwith %}
```

