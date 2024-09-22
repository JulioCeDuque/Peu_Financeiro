from django.shortcuts import render, HttpResponse, HttpResponseRedirect, get_object_or_404, redirect
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as login_django
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.template import loader
from .models import clientes, CadastroFinanceiro
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from django.db.models import Sum, Count
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.utils import timezone



# Create your views here.
@login_required(login_url=('/')) 
def cadastro(request):

    user_belongs_to_group = request.user.groups.filter(name='ADM').exists() | request.user.is_superuser

    if not user_belongs_to_group:
        messages.error(request, "Você não tem permissão para acessar a página Cadastro.")
        return redirect('/home')
    
    if request.method == "GET":
        return render(request, 'internos/cadastro.html')
    else:
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        
        user = User.objects.filter(username=username).first()
        
        if user:
            return HttpResponse('Esse usuario ja existe')
        
        user = User.objects.create_user(username=username, email=email, password=senha)
        user.save()
        
        
        return HttpResponse('CadastroEfetuado')
    
#####################################################################################################################

def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return HttpResponseRedirect('/home')
        return render(request, 'internos/login.html')
    else:
        username = request.POST.get('username')
        senha = request.POST.get('senha')
        
        user = authenticate(username=username, password=senha)
        
        if user:
            login_django(request, user)
            
            return HttpResponseRedirect('/home')
        else:
            messages.error(request, 'Nome de usuário ou senha incorretos.')
            return redirect('/')

#####################################################################################################################
   
@login_required(login_url=('/'))    
def plataforma(request):
    
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')

        try:

            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

                
            total_valor = CadastroFinanceiro.objects.filter(data_pagamento__range=[data_inicio, data_fim]).aggregate(Sum('valor'))['valor__sum']

               
            return render(request, 'internos/plataforma.html', {'total_valor': total_valor})

        except ValueError:
                
            return render(request, 'internos/plataforma.html', {'error_message': 'Formato de data inválido. Use o formato AAAA-MM-DD.'})

    return render(request, 'internos/plataforma.html')
    
def dados_do_grafico(request):
    if request.user.groups.filter(name='ADM').exists():
       
        dados = CadastroFinanceiro.objects.all()
    else:
      
        grupo_do_usuario = request.user.groups.first()
        dados = CadastroFinanceiro.objects.filter(departamento=grupo_do_usuario)

    data_atual = timezone.localtime().date()

    primeiro_dia_semana = data_atual - timedelta(days=data_atual.weekday())
    ultimo_dia_semana = primeiro_dia_semana + timedelta(days=6)

    dados_semana = dados.filter(data_pagamento__range=(primeiro_dia_semana, ultimo_dia_semana)).values('data_pagamento').annotate(total_servicos=Count('id'))

    return JsonResponse(list(dados_semana), safe=False)
    
#####################################################################################################################
    
def filtro_datas_departamento(request):
     
    departamentos = ['Clínica Odontológica', 'Prótese e Materiais Dentários', 'Odontologia Legal social e preventiva', 'Odontopediatria', 'Ortodontia', 'Patologia e Diagnóstico Oral']

    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        departamento_selecionado = request.POST.get('departamento')

        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

            total_valor = CadastroFinanceiro.objects.filter(data_pagamento__range=[data_inicio, data_fim], departamento=departamento_selecionado).aggregate(Sum('valor'))['valor__sum']

            return render(request, 'internos/plataforma.html', {'total_valor': total_valor, 'departamentos': departamentos})

        except ValueError:
            return render(request, 'internos/plataforma.html', {'error_message': 'Formato de data inválido. Use o formato AAAA-MM-DD.', 'departamentos': departamentos})

    return render(request, 'internos/plataforma.html', {'departamentos': departamentos})
    
#####################################################################################################################

def auth_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

#####################################################################################################################

def verificar_cpf(request):
    
    if request.method == 'POST' and request.is_ajax():
       
        cpf = request.POST.get('cpf')

        if clientes.objects.filter(cpf=cpf).exists():
            
            return JsonResponse({'exists': True})

    return JsonResponse({'exists': False})

#####################################################################################################################

@login_required(login_url='/')
def cadastro_externo(request):
    if request.method == 'POST':
        cpf = request.POST.get('cpf')
        
        if clientes.objects.filter(cpf=cpf).exists():
            return JsonResponse({'success': False, 'mensagem_erro': 'Este CPF já está em uso.'})
        else:
            cliente = clientes()
            cliente.cpf = cpf
            cliente.nome = request.POST.get('nome')
            cliente.cep = request.POST.get('cep')
            cliente.endereco = request.POST.get('endereco')
            cliente.numero = request.POST.get('numero')
            cliente.complemento = request.POST.get('complemento')
            cliente.bairro = request.POST.get('bairro')
            cliente.cidade = request.POST.get('cidade')
            cliente.estado = request.POST.get('estado')
            cliente.telefone_principal = request.POST.get('telefone_principal')
            cliente.email = request.POST.get('email')
            cliente.save()
            return JsonResponse({'success': True})

    clientes_data = {
        'clientes': clientes.objects.all(),
    }
    return render(request, 'internos/cadastro_externo.html', clientes_data)

#####################################################################################################################

@login_required(login_url='/')
def cadastro_financeiro(request):
    usuario = request.user
    grupos_usuario = usuario.groups.all() 

    departamentos_permitidos = {
        '26.023 - Clínica Odontológica': ['26.023 - Clínica Odontológica'],
        '26.024 - Prótese': ['26.024 - Prótese'],
        '26.025 - Ortodontia': ['26.025 - Ortodontia'],
        '26.026 - Odontopediatria': ['26.026 - Odontopediatria'],
        '26.027 - Radiologia': ['26.027 - Radiologia'],
        '26.028 - Estomatologia': ['26.028 - Estomatologia'],
        '26.029 - Patologia Oral': ['26.029 - Patologia Oral'],
        '26.030 - Pós-graduação': ['26.030 - Pós-graduação'],
        'Secretaria': ['26.023 - Clínica Odontológica', '26.024 - Prótese', '26.025 - Ortodontia', '26.026 - Odontopediatria', '26.027 - Radiologia', '26.028 - Estomatologia', '26.029 - Patologia Oral', '26.030 - Pós-graduação']
    }

    departamentos = []
    departamento_principal = None

    for grupo in grupos_usuario:
        if grupo.name in departamentos_permitidos:
            departamentos.extend(departamentos_permitidos[grupo.name])
            if not departamento_principal:
                departamento_principal = departamentos_permitidos[grupo.name][0]  

    departamentos = list(set(departamentos))

    if request.method == 'POST':
        cpf = request.POST.get('cpf')

        if clientes.objects.filter(cpf=cpf).exists():
            cliente = clientes.objects.get(cpf=cpf)

            cadastro = CadastroFinanceiro()
            cadastro.cliente = cliente
            cadastro.cpf = request.POST.get('cpf')
            cadastro.valor = request.POST.get('valor')
            cadastro.data_pagamento = request.POST.get('data_pagamento')
            cadastro.forma_pagamento = request.POST.get('forma_pagamento')
            cadastro.chave_seguranca = request.POST.get('chave_seguranca')
            cadastro.departamento = request.POST.get('departamento')
            cadastro.descricao = request.POST.get('descricao')
            cadastro.save()

            return JsonResponse({'status': 'Success'})

        else:
            return JsonResponse({'status': 'Error', 'message': 'Cliente não encontrado.'})

    return render(request, 'internos/cadastro_financeiro.html', {'departamentos': departamentos, 'departamento_principal': departamento_principal})


def verificar_cliente(request):
    cpf = request.GET.get('cpf', None)

    data = {
        'cliente_existe': False,
        'nome_cliente': None,
        'mensagem': ''
    }

    if cpf:
        if clientes.objects.filter(cpf=cpf).exists():
            cliente = clientes.objects.get(cpf=cpf)
            data['cliente_existe'] = True
            data['nome_cliente'] = cliente.nome
        else:
            data['mensagem'] = 'Não encontrado no sistema.'

    return JsonResponse(data)

#####################################################################################################################

@login_required(login_url=('/'))   
def lista_clientes(request):
    is_admin = request.user.groups.filter(name='ADM').exists() or request.user.groups.filter(name='Secretaria').exists()

    cliente = {
        'cliente': clientes.objects.all(),
        'is_admin' : is_admin
    }
    return render(request, 'internos/lista_clientes.html', cliente)

#####################################################################################################################

@login_required(login_url='/')
def editar_cliente(request, id):
    # Buscar o cliente pelo ID ou retornar 404 se não encontrado
    cliente = get_object_or_404(clientes, id=id)
    mensagem_erro = None
    

    if request.method == 'POST':
        # Atualizar os dados do cliente com os dados do formulário
        cliente.nome = request.POST.get('nome')
        cliente.cep = request.POST.get('cep')
        cliente.endereco = request.POST.get('endereco')
        cliente.numero = request.POST.get('numero')
        cliente.complemento = request.POST.get('complemento')
        cliente.bairro = request.POST.get('bairro')
        cliente.cidade = request.POST.get('cidade')
        cliente.estado = request.POST.get('estado')
        cliente.telefone_principal = request.POST.get('telefone_principal')
        cliente.email = request.POST.get('email')
        cliente.save()
            
    
    # Passar o cliente e mensagem de erro para o template
    clientes_data = {
        'cliente': cliente,
        'mensagem_erro': mensagem_erro
    }

    return render(request, 'internos/editar_cliente.html', clientes_data)

#####################################################################################################################

def servicos_cliente(request, cpf):

   cliente = clientes.objects.get(cpf=cpf)
   servicos = CadastroFinanceiro.objects.filter(cpf=cpf)
  
   
   return render(request, 'internos/servicos.html', {'servicos': servicos, 'cliente': cliente})

#####################################################################################################################

@login_required(login_url=('/'))
def lista_usuarios(request):
    user_belongs_to_group = request.user.groups.filter(name='ADM').exists() | request.user.is_superuser

    if not user_belongs_to_group:
        messages.error(request, "Você não tem permissão para acessar a página Usuarios.")
        return redirect('/home')

    usuarios = User.objects.all()

    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        action = request.POST.get('action')

        if action == 'delete':
        
            group_id = request.POST.get('group')
            group = Group.objects.get(pk=group_id)
            usuario = User.objects.get(pk=usuario_id)
            usuario.groups.remove(group)
            messages.success(request, f'Grupo de {usuario.username} alterado para {group.name}.')
            return HttpResponseRedirect('/internos')

        elif action == 'change_group':

            group_id = request.POST.get('group')
            group = Group.objects.get(pk=group_id)
            usuario = User.objects.get(pk=usuario_id)
            usuario.groups.add(group)
            messages.success(request, f'Grupo de {usuario.username} alterado para {group.name}.')
            return HttpResponseRedirect('/internos')
        
        elif action == 'delete_usuario':

            if request.user.is_superuser:
                usuario = User.objects.get(pk=usuario_id)
                usuario.delete()
                return HttpResponseRedirect('/internos')
            else:
                messages.error(request, "Você não tem permissão para excluir usuários.")
                return HttpResponseRedirect('/internos')

        
        elif action == 'reset_password':

            usuario = User.objects.get(pk=usuario_id)
            send_password_reset_email(request, usuario)
            messages.success(request, f'E-mail de redefinição de senha enviado para {usuario.username}.')
            return HttpResponseRedirect('/internos')

    groups = Group.objects.all()
    return render(request, 'internos/lista_usuarios.html', {'usuarios': usuarios, 'groups': groups})

#####################################################################################################################

def send_password_reset_email(request, usuario):
    token_generator = default_token_generator
    current_site = get_current_site(request)
    email_subject = 'Redefinir sua senha'
    email_template_name = 'internos/reset_password.html'
    context = {
        'user': usuario,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(usuario.pk)),
        'token': token_generator.make_token(usuario),
        'protocol': 'https' if request.is_secure() else 'http',
    }
    html_email = render_to_string(email_template_name, context)
    text_email = strip_tags(html_email)
    
    
    email = EmailMultiAlternatives(email_subject, text_email, None, [usuario.email])
    email.attach_alternative(html_email, "text/html")
    email.send()

#####################################################################################################################

# @login_required(login_url=('/'))
# def teste_cliente(request):
#     if request.user.groups.filter(name='ADM').exists() | request.user.groups.filter(name='Secretaria').exists():
    
#         projeto = {
#             'projeto': CadastroFinanceiro.objects.all()
#         }

#     else:

#         grupos_do_usuario = request.user.groups.all()
#         departamentos_do_usuario = [grupo.name for grupo in grupos_do_usuario]
#         projeto = {
#             'projeto': CadastroFinanceiro.objects.filter(departamento__in=departamentos_do_usuario)
#         }

#     return render(request, 'internos/teste_cliente.html', projeto)

#     @login_required(login_url=('/'))

def teste_cliente(request):
    is_admin = request.user.groups.filter(name='ADM').exists() or request.user.groups.filter(name='Secretaria').exists()
    
    if is_admin:
        if is_admin:
            projeto = CadastroFinanceiro.objects.all()
            contexto = {
                'projeto': projeto,
                'is_admin': is_admin
            }

        if request.method == 'POST' and 'projeto_id' in request.POST:
            projeto_id = request.POST['projeto_id']
            projeto_a_excluir = get_object_or_404(CadastroFinanceiro, pk=projeto_id)
            projeto_a_excluir.delete()
            return redirect('/relatorios')

        if request.method == 'POST' and 'projeto_pago' in request.POST:
            projeto_pago = request.POST['projeto_pago']
            projota = CadastroFinanceiro.objects.get(pk=projeto_pago)
            projota.pago = True
            projota.save()
            return redirect('/relatorios')

        if request.method == 'POST' and 'projeto_despago' in request.POST:
            projeto_despago = request.POST['projeto_despago']
            ta_despago = CadastroFinanceiro.objects.get(pk=projeto_despago)
            ta_despago.pago = False
            ta_despago.save()
            return redirect('/relatorios')

    else:

        grupos_do_usuario = request.user.groups.all()
        departamentos_do_usuario = [grupo.name for grupo in grupos_do_usuario]
        contexto = {
            'projeto': CadastroFinanceiro.objects.filter(departamento__in=departamentos_do_usuario)
        }

    return render(request, 'internos/teste_cliente.html', contexto)

#####################################################################################################################

@login_required(login_url=('/'))
def informacoes_gerais(request, id):
    servico = CadastroFinanceiro.objects.get(id=id)

    if request.user.groups.filter(name='ADM').exists() | request.user.groups.filter(name='Secretaria').exists() | request.user.groups.filter(name=servico.departamento).exists():

        cliente = clientes.objects.filter(cpf=servico.cpf)
        return render(request, 'internos/descricao.html', {'servico': servico, 'cliente': cliente})
    
    else:

        return HttpResponse("Você não tem permissão para visualizar estas informações.")
    
#####################################################################################################################

@login_required(login_url=('/'))
def exportar_dados(request):
    if request.method == 'POST' and 'action' in request.POST:

        if request.POST['action'] == 'exportar':

            data_inicio = request.POST.get('data_inicio')
            data_fim = request.POST.get('data_fim')

            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')

            if request.user.groups.filter(name='ADM').exists() | request.user.groups.filter(name='Secretaria').exists():

                dados_filtrados = CadastroFinanceiro.objects.filter(data_pagamento__range=(data_inicio, data_fim))

            else:

                grupos_do_usuario = request.user.groups.all()
                departamentos_do_usuario = [grupo.name for grupo in grupos_do_usuario]
                dados_filtrados = CadastroFinanceiro.objects.filter(data_pagamento__range=(data_inicio, data_fim), departamento__in=departamentos_do_usuario)

            csv_content = "CPF;Nome;CEP;Endereço;Número;Complemento;Bairro;Cidade;Estado;Telefone principal;E-mail;Valor;Data Pagamento;Forma Pagamento;Chave Segurança;Departamento\n"
            for dado in dados_filtrados:
                cliente = clientes.objects.get(cpf=dado.cpf)
                data_pagamento_formatada = dado.data_pagamento.strftime('%d/%m/%Y')
                csv_content += f"{cliente.cpf};{cliente.nome};{cliente.cep};{cliente.endereco};{cliente.numero};{cliente.complemento};{cliente.bairro};{cliente.cidade};{cliente.estado};{cliente.telefone_principal};{cliente.email};{dado.valor};{data_pagamento_formatada};{dado.forma_pagamento};{dado.chave_seguranca};{dado.departamento}\n"

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="dados_exportados.csv"'
            response.write(csv_content)
            return response