# Permafrost Forms
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.fields import CharField, ChoiceField, BooleanField
from django.forms.models import ModelMultipleChoiceField
from django.forms.widgets import CheckboxInput
from django.utils.translation import gettext_lazy as _
from .models import PermafrostRole, get_optional_by_category, get_choices

CHOICES = [('', _("Choose Role Type"))] + get_choices()

LABELS = {
    'name': _('Role Name'),
    'category': _('Role Type')
}

def assemble_optiongroups_for_widget(permissions):
    choices = []
    optgroups = {}
    if permissions:
        for perm in permissions:
            if perm.content_type.name in optgroups:
                optgroups[perm.content_type.name].append((perm.pk, perm.name,))
            else:
                optgroups[perm.content_type.name] = [(perm.pk, perm.name,)]

    for model_name, options in optgroups.items():
        choices.append([model_name, options])
    
    return choices

def bootstrappify(fields):
    for field in fields:
        widget = fields[field].widget
        if not isinstance(widget, CheckboxInput):
            if 'class' in widget.attrs:
                widget.attrs['class'] =  widget.attrs['class'] + " form-control"
            else:
                widget.attrs.update({'class':'form-control'})

class SelectPermafrostRoleTypeForm(ModelForm):
    name = CharField(required=False)
    description = CharField(required=False)
    category = ChoiceField(choices=CHOICES)
    
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)
        labels = LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bootstrappify(self.fields)

    


class PermafrostRoleCreateForm(ModelForm):
    permissions = ModelMultipleChoiceField(queryset=Permission.objects.all(), required=False)
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category', 'permissions')
        labels = LABELS

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site', Site.objects.get_current())
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = CHOICES
        
        category = self.initial.get(
            'category', 
            self.data.get('category', None)
        )
        
        if self.instance:
            category = self.instance.category if self.instance.category else category
        
        if category:
            all_optional_permissions = get_optional_by_category(category=category)
            ids = [perm.pk for perm in all_optional_permissions]
        
            self.fields['permissions'].queryset = Permission.objects.filter(id__in=ids)

        bootstrappify(self.fields)
        
    def save(self, commit=True):
        self.instance.site = self.site
        instance = super().save(commit)        
        category = instance.category

        if 'permissions' in self.cleaned_data:
            perm_ids = []
            if category:
                perm_ids = self.cleaned_data['permissions']
            if perm_ids:
                instance.permissions_set(Permission.objects.filter(id__in=perm_ids))
            else:
                instance.permissions_clear()
        return instance

    def clean_name(self):
        name = self.cleaned_data['name']
        name_exists = False
       
        if self.instance:  ## on update check if name change exists

            if 'name' in self.changed_data:
                name_exists = PermafrostRole.objects.filter(

                    name=name, 
                    site=self.site,

                ).exclude(pk=self.instance.pk).first()
            
        else:

            try:
                name_exists = PermafrostRole.objects.get(
                    name=name, 
                    site=self.site
                )
            except PermafrostRole.DoesNotExist:
                pass
        
        if name_exists:
            raise ValidationError('Role with this name already exists')

        # Always return field
        return name

class PermafrostRoleUpdateForm(PermafrostRoleCreateForm):
    """
     Form used to display role detail
     Only allowed to edit optional permissions, name and description
     Category and required permissions stay locked
    """
    deleted = BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['category'].widget.attrs.update({'readonly': True, 'disabled': True})
        self.fields['category'].disabled = True
        self.fields['category'].required = False
        self.fields['category'].choices = [choice for choice in CHOICES if choice[0] == self.instance.category]
        self.fields['category'].initial = self.instance.category
        ## limit choices to saved category
        self.fields['deleted'].initial = self.instance.deleted

    def save(self, commit=True):
        if self.cleaned_data['deleted']:
            self.instance.deleted = self.cleaned_data['deleted']
        instance = super().save(commit)
        return instance
        
