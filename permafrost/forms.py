# Permafrost Forms
from django.contrib.auth.models import Permission
from django.forms import ModelForm, MultipleChoiceField, CheckboxSelectMultiple
from django.forms.fields import CharField, ChoiceField
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

class SelectPermafostRoleTypeForm(ModelForm):
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
            
            self.fields[f'required_{category}_perms'] = MultipleChoiceField(label=_("Required Permissions"), initial=initial, choices=required_choices, widget=CheckboxSelectMultiple(attrs={'readonly':True, 'disabled': True}))
            self.fields[f'optional_{category}_perms'] = MultipleChoiceField(label=_("Optional Permissions"), choices=optional_choices, widget=CheckboxSelectMultiple())

    def save(self, commit=True):
        instance = super().save(commit)
        category = self.cleaned_data.get('category', None)
        perm_ids =[]
        if category:
            perm_ids = self.data.getlist(f'optional_{category}_perms')
        if perm_ids:
            instance.permissions_set(Permission.objects.filter(id__in=perm_ids))
        return instance

class PermafrostRoleUpdateForm(PermafrostRoleCreateForm):
     
     def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True

            if self.instance:
                
                if self.instance.category: 
                    
                    required_perms = self.instance.required_permissions()
                    optional_perms = self.instance.optional_permissions()
                    required_choices = assemble_optiongroups_for_widget(required_perms)
                    optional_choices = assemble_optiongroups_for_widget(optional_perms)
                    initial = [perm.pk for perm in required_perms]

                    available_optional_ids = [permission.id for permission in optional_perms]
                    all_permissions = self.instance.permissions().all()
                    preselected_optional = [permission.id for permission in all_permissions if permission.id in available_optional_ids]

                    self.fields.update({
                        f'required_{self.instance.category}_perms': MultipleChoiceField(
                            label=_("Required Permissions"), 
                            initial=initial, 
                            choices=required_choices, 
                            widget=CheckboxSelectMultiple(attrs={
                                'readonly':True, 
                                'disabled': True
                            })
                        ),

                        f'optional_{self.instance.category}_perms': MultipleChoiceField(
                            label=_("Optional Permissions"), 
                            initial=preselected_optional, 
                            choices=optional_choices, 
                            widget=CheckboxSelectMultiple()
                        )
                    })
