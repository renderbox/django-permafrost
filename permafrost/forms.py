# Permafrost Forms
from django.contrib.auth.models import Permission
from django.forms import ModelForm, MultipleChoiceField, CheckboxSelectMultiple
from django.forms.fields import BooleanField, CharField, ChoiceField
from django.forms.forms import Form
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _
from .models import PermafrostRole, get_optional_by_category, get_required_by_category, get_choices

CHOICES = [('', _("Choose Role Type"))] + get_choices()

def assemble_optiongroups_for_widget(permissions):
    choices = []
    optgroups = {}
    if permissions:
        for perm in permissions:
            if perm.content_type.model in optgroups:
                optgroups[perm.content_type.model].append((perm.pk, perm.name,))
            else:
                optgroups[perm.content_type.model] = [(perm.pk, perm.name,)]

    for model_name, options in optgroups.items():
        choices.append([model_name, options])
    
    return choices

class SelectPermafrostRoleTypeForm(ModelForm):
    name = CharField(required=False)
    description = CharField(required=False, widget=Textarea())
    category = ChoiceField(choices=CHOICES)
    
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)


class PermafrostRoleCreateForm(ModelForm):
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)
        widgets = {
            'description': Textarea(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].choices = CHOICES
        category = self.initial.get('category', None)
        
        if category:  
              
            required_perms = get_required_by_category(category)
            optional_perms = get_optional_by_category(category)
            required_choices = assemble_optiongroups_for_widget(required_perms)
            optional_choices = assemble_optiongroups_for_widget(optional_perms)
            
            initial = [perm.pk for perm in required_perms]
            
            self.fields[f'required_{category}_perms'] = MultipleChoiceField(label=_("Required Permissions"), initial=initial, choices=required_choices, widget=CheckboxSelectMultiple(attrs={'readonly':True, 'disable': True}))
            self.fields[f'optional_{category}_perms'] = MultipleChoiceField(label=_("Optional Permissions"), choices=optional_choices, widget=CheckboxSelectMultiple(), required=False)

    def save(self, commit=True):
        instance = super().save(commit)
        category = self.cleaned_data.get('category', None)
        perm_ids =[]
        if category:
            perm_ids = self.data.getlist(f'optional_{category}_perms')
        if perm_ids:
            instance.permissions_set(Permission.objects.filter(id__in=perm_ids))
        return instance

class PermafrostRoleUpdateForm(Form):
    """
     Form used to display role detail
     Only allowed to edit optional permissions, name and description
     Category and required permissions stay locked
    """
    name = CharField(required=False)
    description = CharField(required=False, widget=Textarea())
    category = ChoiceField(required=False, choices=CHOICES, disabled=True) 
    deleted = BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['category'].widget.attrs['readonly'] = True
        if 'id' in self.initial:
            if self.initial:
                
                for field in self.fields:
                    self.fields[field].initial = self.initial[field]
        
                if 'category' in self.initial:
                    category = self.initial['category']

                    required_perms = get_required_by_category(category)
                    optional_perms = get_optional_by_category(category)
                    required_choices = assemble_optiongroups_for_widget(required_perms)
                    optional_choices = assemble_optiongroups_for_widget(optional_perms)
                    initial = [perm.pk for perm in required_perms]
                    
                    available_optional_ids = [permission.id for permission in optional_perms]
                    preselected_optional = [id for id in self.initial['all_permissions_ids'] if id in available_optional_ids]

                    self.fields.update({
                        f'required_{category}_perms': MultipleChoiceField(
                            label=_("Required Permissions"), 
                            initial=initial, 
                            choices=required_choices, 
                            widget=CheckboxSelectMultiple(attrs={'readonly':True, 'disabled': True}),
                            required=False
                        ),

                        f'optional_{category}_perms': MultipleChoiceField(
                            label=_("Optional Permissions"), 
                            initial=preselected_optional, 
                            choices=optional_choices, 
                            widget=CheckboxSelectMultiple(),
                            required=False,
                        )
                    })