from django.contrib import admin

from mahakupdate.models import Mtables, Kala, Factor, FactorDetaile, WordCount, Category, Kardex, Person, KalaGroupinfo, \
    Storagek, Mojodi


# Register your models here.


class MtablesAdmin(admin.ModelAdmin):
    list_display = ['__str__','name', 'description', 'in_use','update_priority','last_update_time','row_count','cloumn_count']
    # list_filter = ['description','name', 'in_use']
    list_editable = ['description', 'in_use','update_priority']
    search_fields = ['name', 'description', 'in_use','update_priority']

    class Meta:
        model = Mtables


class KalaAdmin(admin.ModelAdmin):
    list_display = ['__str__','name', 'code','category','s_m_ratio','total_sale']
    list_filter = ['category']
    list_editable = ['category']
    search_fields = ['name', 'code']

    class Meta:
        model = Kala
class FactorAdmin(admin.ModelAdmin):
    list_display = ['pdate', 'code','create_time','mablagh_factor','takhfif','darsad_takhfif']
    # list_filter = ['name','code']
    # list_editable = ['description', 'in_use']
    # search_fields = ['name', 'code']

    class Meta:
        model = Factor

class FactorDetaileAdmin(admin.ModelAdmin):
    list_display = ['code_factor', 'kala','count','mablagh_vahed','mablagh_nahaee']
    # list_filter = ['name','code']
    # list_editable = ['description', 'in_use']
    # search_fields = ['name', 'code']

    class Meta:
        model = FactorDetaile

class WordCountAdmin(admin.ModelAdmin):
    list_display = ['word','count']
    # list_filter = ['name','code']
    # list_editable = ['description', 'in_use']
    search_fields = ['word']

    class Meta:
        model = WordCount

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['__str__','name','parent','level']
    list_filter = ['level','parent',]
    list_editable = ['name','parent','level']
    search_fields = ['name','parent','level']

    class Meta:
        model = Category

class KardexAdmin(admin.ModelAdmin):
    list_display = ['__str__','date','stock','code_kala','kala','count','ktype','percode','storage','warehousecode','averageprice','sync_mojodi']
    list_filter = ['warehousecode','sync_mojodi']
    list_editable = ['sync_mojodi']
    search_fields = ['pdate','count','code_kala','stock']

    class Meta:
        model = Kardex
class MojodiAdmin(admin.ModelAdmin):
    list_display = ['__str__','stock','total_stock','code_kala','kala','storage','warehousecode','averageprice','mojodi_roz','mojodi_roz_arzesh']
    list_filter = ['warehousecode']
    # list_editable = ['name','parent','level']
    search_fields = ['code_kala','stock']

    class Meta:
        model = Mojodi


class PersonAdmin(admin.ModelAdmin):
    list_display = ['__str__','code','name','lname','group']
    # list_filter = ['level','parent',]
    # list_editable = ['name','parent','level']
    search_fields = ['name','code','lname','group']

    class Meta:
        model = Person


class KalaGroupinfoAdmin(admin.ModelAdmin):
    list_display = ['__str__','id','code','contain','cat3','cat2','cat1']
    # list_filter = ['level','parent',]
    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = KalaGroupinfo

class StoragekAdmin(admin.ModelAdmin):
    list_display = ['__str__','code']
    # list_filter = ['level','parent',]
    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = Storagek

admin.site.register(Mtables, MtablesAdmin)
admin.site.register(Kala, KalaAdmin)
admin.site.register(Factor, FactorAdmin)
admin.site.register(FactorDetaile, FactorDetaileAdmin)
admin.site.register(WordCount, WordCountAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Kardex, KardexAdmin)
admin.site.register(Mojodi, MojodiAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(KalaGroupinfo, KalaGroupinfoAdmin)
admin.site.register(Storagek, StoragekAdmin)
