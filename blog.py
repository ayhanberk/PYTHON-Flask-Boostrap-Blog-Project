from click import confirm
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request 
from flask_mysqldb import MySQL #flask ve sql bağlantısında kullanılıyor
from wtforms import Form,StringField,TextAreaField,PasswordField,validators #sitedeki string text password alanlarının oluşturmakta kullanılıyor.
from passlib.hash import sha256_crypt #parola şifreleme işlemlerinde kullanılımakta
from functools import wraps #kullanıcı giriş yaptığını ve yapmak istediği işlem için yetkisi olduğunun kontrolünde kullanılmakta

#KULLANICI GİRİŞ KONTROL DECORATOR'I
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfaı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))
    return decorated_function
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#Kayıt formu için gerekli bilgilerin kullanıcıdan alınmasını sağlayan class bölümü.
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=3, max=50,message="Lütfen minimum 4 karakter olabilir(max 25)")])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min=3,max=35)])
    email = StringField("Email Adresi",validators=[validators.Email(message="Lütfen Geçerli Bir Emaiil Adresi Giriniz...")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen bir parola Belirleyiniz."),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor...")])
    confirm = PasswordField("Parola Doğrula")
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////   

#KULLANICI GİRİŞ FORMU
class LoginForm(Form):
    username = StringField("Kullanıcı adı")
    password = PasswordField("Parola")
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////   

#MAKALE FORM FORMATI
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#FLASK VE SQL ARASINDAKİ BAĞLANTIYI OLUŞTURMA
app = Flask(__name__)
app.secret_key = "Bl0gs3cr3tK3yZ"
app.config["MYSQL_HOST"] = "localhost" #db bağlantı ipsini giriyoruz.
app.config["MYSQL_USER"] = "root" #
app.config["MYSQL_PASSWORD"] = "" #db şifresi var ise onu giriyoruz
app.config["MYSQL_DB"] = "myblog" #db deki sql veritabanı ismi
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
sql = MySQL(app) #mysql kütüphanesini sql adına atıyoruz sql tabanına veri aktarmakta yazım kolaylığı olması için
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////  

#ANA SAYFA 
@app.route("/")
def index():
    return render_template("main.html")
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////  

#KONTROL PANELİ SAYFASI
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = sql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    
    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#HAKKIMIZDA SAYFASI
@app.route("/about")
def about():
    return render_template("about.html")
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////  

#MAKALELER SAYFASI
@app.route("/articles")
def articles():
    cursor = sql.connection.cursor()
    
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////  

#MAKALE EKLEME SAYFASI
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        
        cursor = sql.connection.cursor()
        
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        
        cursor.execute(sorgu,(title,session["username"],content))
        
        sql.connection.commit()
        cursor.close()
        
        flash("Makale Başarıyla Eklendi.","success")
        return redirect(url_for("dashboard"))
         
    return render_template("addarticle.html",form = form)
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#MAKALE DETAY SAYFASI
@app.route("/article/<string:id>")
def article(id):
    cursor = sql.connection.cursor()
    
    sorgu = "Select * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")    
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#MAKALE DÜZENLEME GÜNCELLEME SAYFASI
@app.route("/edit/<string:id>",methods = ["GET","POST"]) #get ve post işlemi yapılacağı için metotlara ekledik.
#<string:id> komutu sayesinde veritabanında biriken herhangi bir idli sayfaya tıklanınca onun id numarası <string:id> bu komut yerıne geçerek onun edit sayfası açılacak
#eğer öyle bir sayfa yok ise böyle bir sayfa mevcut değil bilgisi verilecek
@login_required
def update(id):
    if request.method == "GET": #site üzerinden veriyi çekmek için kullandığımız komut
        cursor = sql.connection.cursor()#sql bağlantısını ve işlem yapmamız için cursor oluşturma işlemini gerçekleştiriyoruz.
        sorgu = "Select * from articles where id = %s and author = %s" #istenen id ve yazar bilgilerinin kontrollerini sağlıyoruz.
        result = cursor.execute(sorgu,(id,session["username"])) #sorgudaki karşılaştırma bilgilerini result'a atama işlemi yapıyoruz.
        
        if result == 0:#eğer herhangi bir sonuç çıkmaz ise bu koşula giriş yapıyor.
            flash("Böyle bir makale yok VEYA bu işlem için yetkiniz yok...","danger")#kullanıcıya bilgilendirme yapılıyor.
            return redirect(url_for("index")) # ana sayfaya dönüş yapıyoruz.           
        else: #sorgu sonucu bir sonuç elde edildiğinde bu koşula giriyor.
            article = cursor.fetchone() #veritabanından istenilen bilgileri çekiyoruz./fetchall bütün bilgileri /fetchone sadece istenilen bilgileri çekiyor.
            form = ArticleForm() #article form tasarımını çağırıyoruz.
            form.title.data = article["title"] #sistemdeki eski kayıtlı olan başlığı db den çekiyoruz.
            form.content.data = article["content"]#sistemdeki eski kayıtlı olan içeriği dbden çekiyoruz.
            return render_template("update.html",form = form)# güncelleme sayfasına geçiyoruz.
            
    else:
        # POST REQUEST  
        form = ArticleForm(request.form)
        if request.method == "POST":
        
            newTitle = form.title.data #ve yeni girilen başlığı eskisinin yerine yazıyoruz.
            newContent = form.content.data#yeni girilen içeriği eski içeriğin yerine yazıyoruz.
        
            sorgu2 = "Update articles Set title = %s, content = %s where id = %s"
            cursor = sql.connection.cursor()
            cursor.execute(sorgu2,(newTitle,newContent,id))
            sql.connection.commit()
            flash("Makale Başarıyla Güncellendi....","success")
            return redirect(url_for("dashboard"))
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#MAKALE SİLME SAYFASI
@app.route("/delete/<string:id>")#<string:id> bu komut sayesınde delete/(herhangi-bir-sayfa) geldiğinde bu komutun içine girecek.
@login_required
def delete(id):
    cursor = sql.connection.cursor()
    
    sorgu = "Select * From articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    
    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        
        cursor.execute(sorgu2,(id,))
        
        sql.connection.commit()
        flash("Makale Başarıyla Silindi...","success")
        return redirect(url_for("dashboard"))
        
    else:
        flash("Böyle bir makale yok veya bu işlem için yetkiniz yok","danger")
        return redirect(url_for("index"))
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
 
#GİRİŞ YAP SAYFASI
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
    
        cursor = sql.connection.cursor()
        sorgu = "Select * From users where username = %s"
    
        result = cursor.execute(sorgu,(username,)) #girilen kullanıcı adı ile db deki kullanıcı isimleri karışaltırılır ve result'a atanır.
        if result > 0:#eğer ki Böyle bir kullanıcı ismi var ise bu koşula girer.
            data = cursor.fetchone() #girilen username deki kullanıcının db bilgilerini alıyoruz.
            real_password = data["password"] #kullanıcının password bilgilerini real_password'a atıyoruz.
            if sha256_crypt.verify(password_entered,real_password):#sha256 yardımı ile kullanıcının gizlenen şifresi ile giriş yaparken kullandığı şifreyi kartışaltırıyoruz.
                flash("Başarıyla Giriş Yapıldı...","success")
            
                session["logged_in"] = True #session yardımı ile giriş yaptıktan sonra logged_in değerini true yapıyoruz ve bu değere istediğimiz yerden ulaşabiliyoruz.
                #eğer giriş yapılmadıysa bu değer false olarak kalıcağı için kullanıcının giriş yapıp yapmadığını görebiliyoruz.
                session["username"] = username #kullanıcının kullanıcı adını istediğimiz biyerden ulaşabilmek için session komutunu kullanıyoruz.
                session["name"] = data["name"]#kullanıcı giriş yaptığında ismini başka bir sayafada kullanmak istediğimizde bu şekilde ulaşabiliyoruz.
                return redirect(url_for("index"))#kullanıcı giriş yaptıktan sonra anasayfaya yönlendiriyoruz.
            else:
                flash("Parolanızı Yanlış Girdiniz.","danger")
                return redirect(url_for("login"))
        else: # db kontrolu sonucu kullancı adıyla uyuşan biri bulunmazsa bu koşula giriyor.
            flash("Böyle Bir Kullanıcı Bulunmamaktadır...","danger")
            return redirect(url_for("login"))#kullanıcı ismini yanlış olduğu için tekrardan login sayfasına yönlendiriliyor.
    return render_template("login.html",form = form)
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////  

#ÇIKIŞ YAP SAYFASI
@app.route("/logout")
def logout():
    session.clear() #session bilgisini silerek site üzerindeki session bilgilerini temizliyoruz bu sayede çıkış yapılmış oluyor.
    flash("Başarıyla Çıkış Yapılmıştır...","success")
    return redirect(url_for("index"))
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////  

#KAYIT OL SAYFASI
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    
    if request.method == "POST" and form.validate(): #kullanıcı kayıt formunu doğru şekilde doldurmus ise siteden db ye post yapılır ve bu if komutuna girer.
        name = form.name.data #formdan gelen name datasını name ismine atar.
        username = form.name.data#formdan gelen username datasını username ismine atar.
        email = form.email.data #formadan gelen email adresinin datasını email ismine atar.
        password = sha256_crypt.encrypt(form.password.data)#formdan gelen kullanıcı şifresini sha256 yardımı ile encrypt şeklinde şifreylerek password ismine atar.
        
        cursor = sql.connection.cursor()#db de işlem yapabilmek için cursor oluşturuyoruz.
        
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"#forumdan gelen bilgileri databasein içine aktarmak için kullanılan sorgu komutu.
        cursor.execute(sorgu,(name,email,username,password)) #database'e yaptığımız sorgu komutu ve yazılacak bilgileri demet biçiminde yazıyoruz.
        sql.connection.commit()#db üzerinde değişiklik yaptığımız için kullanmamız gereken komut.
        cursor.close()#sql bağlatısını kapatıyoruz bu şekilde arkaplanda gereksiz kaynak kullanmasını engelliyoruz.
        
        flash("Kayıt işlemi başarıyla gerçekleşti...","success")#işlemlerin ardından açılan sayfada mesaj paylaşmamıza olanak sağlayan komut bu sayede kullanıcıya bilgi verebiliyoruz.
        return redirect(url_for("login"))#kayıt işlemi başarıyla gerçekleşirse gönderilecek sayfası seçiyoruz
        #redirect sayfa yöneldirme olarak kullanılıyor - url_for komutu ise fonksiyon ismi yardımıyla bu fonksiyonu kullanan sayfaya yöneldiriliyor.
    else:
        return render_template("register.html",form = form)
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////  

#ARAMA YAPMA PROGRAMI
@app.route("/search", methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        
        cursor = sql.connection.cursor()
        
        sorgu = "Select * from articles where title like '%" + keyword + "%' "
        
        result = cursor.execute(sorgu)
        
        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    app.run(debug = True)