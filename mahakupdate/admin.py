from django.contrib import admin

from mahakupdate.models import Mtables, Kala, Factor, FactorDetaile, WordCount, Category, Kardex, Person, KalaGroupinfo, \
    Storagek, Mojodi, Sanad, SanadDetail, AccCoding, ChequesRecieve


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


class SanadAdmin(admin.ModelAdmin):
    list_display = ['__str__','code','tarikh','sharh']
    # list_filter = ['level','parent',]
    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = Sanad

class SanadDetailAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'code','tarikh','date', 'kol', 'moin', 'tafzili', 'sharh', 'bed', 'bes', 'curramount','is_analiz','cheque_id','syscomment']
    list_filter = ['kol', 'moin', 'tafzili']
    list_editable = ['is_analiz']
    search_fields = ['tarikh','date', 'kol', 'moin', 'tafzili', 'sharh', 'bed', 'bes', 'curramount','cheque_id']

    class Meta:
        model = SanadDetail

class AccCodingAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'code', 'name', 'level']
    list_filter = ['code', 'name', 'level']

    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = AccCoding



class ChequesRecieveAdmin(admin.ModelAdmin):
    list_display = ('id_mahak', 'cheque_id', 'cheque_row', 'issuance_tarik', 'issuance_date', 'cheque_tarik', 'cheque_date', 'cost', 'bank_name', 'bank_branch', 'account_id', 'description', 'status', 'per_code')
    # list_display = ('id_mahak' , 'cheque_row', 'issuance_tarik', 'issuance_date', 'cheque_tarik', 'cheque_date', 'cost', 'bank_name', 'bank_branch', 'account_id', 'description', 'status', 'per_code')
    search_fields = ('cheque_id', 'bank_name', 'status')


    class Meta:
        model = ChequesRecieve





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
admin.site.register(Sanad, SanadAdmin)
admin.site.register(SanadDetail, SanadDetailAdmin)
admin.site.register(AccCoding, AccCodingAdmin)
admin.site.register(ChequesRecieve, ChequesRecieveAdmin)
