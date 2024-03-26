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
        # Verificar se o usuário já está autenticado
        if request.user.is_authenticated:
            return HttpResponseRedirect('/plataforma')
        return render(request, 'internos/login.html')
    else:
        username = request.POST.get('username')
        senha = request.POST.get('senha')
        
        user = authenticate(username=username, password=senha)
        
        if user:
            login_django(request, user)
            
            return HttpResponseRedirect('/plataforma')
        else:
            messages.error(request, 'Nome de usuário ou senha incorretos.')
            # Redirecionar de volta para a mesma página
            return redirect('/')

#####################################################################################################################
   
@login_required(login_url=('/'))    
def plataforma(request):
    
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')

        try:
                # Convertendo strings em objetos de data
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

                # Consulta ao banco de dados para calcular o total dentro do intervalo de datas especificado
            total_valor = CadastroFinanceiro.objects.filter(data_pagamento__range=[data_inicio, data_fim]).aggregate(Sum('valor'))['valor__sum']

                # Retornando a página com o resultado da consulta
            return render(request, 'internos/plataforma.html', {'total_valor': total_valor})

        except ValueError:
                # Tratamento de erro se as datas não forem válidas
            return render(request, 'internos/plataforma.html', {'error_message': 'Formato de data inválido. Use o formato AAAA-MM-DD.'})

    return render(request, 'internos/plataforma.html')
    # usuarios = User.objects.all()
    # if request.method == 'POST':
    #     usuario_id = request.POST.get('usuario_id')
    #     usuario = User.objects.get(pk=usuario_id)
    #     usuario.delete()
    #     return HttpResponseRedirect('/plataforma')
    # return render(request, 'internos/plataforma.html', {'usuarios': usuarios})
    
def dados_do_grafico(request):
    if request.user.groups.filter(name='ADM').exists():
        # Se o usuário pertencer ao grupo "ADM", ele pode ver todos os dados
        dados = CadastroFinanceiro.objects.all()
    else:
        # Caso contrário, ele só pode ver os dados relacionados ao seu grupo
        grupo_do_usuario = request.user.groups.first()
        dados = CadastroFinanceiro.objects.filter(departamento=grupo_do_usuario)

    # Obtém a data e hora local atual
    data_atual = timezone.localtime().date()

    # Calcula o primeiro dia da semana (segunda-feira) e o último dia da semana (domingo) para a semana atual
    primeiro_dia_semana = data_atual - timedelta(days=data_atual.weekday())
    ultimo_dia_semana = primeiro_dia_semana + timedelta(days=6)

    # Filtra os dados do banco de dados para obter apenas os registros com data de pagamento dentro da semana atual
    dados_semana = dados.filter(data_pagamento__range=(primeiro_dia_semana, ultimo_dia_semana)).values('data_pagamento').annotate(total_servicos=Count('id'))

    # Converte os dados para o formato JSON e retorna como uma resposta JSON
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
    # Redirecione para a página inicial, por exemplo
    return HttpResponseRedirect('/')

#####################################################################################################################

def verificar_cpf(request):
    # Verifica se a requisição é do tipo POST e se é uma requisição AJAX
    if request.method == 'POST' and request.is_ajax():
        # Obtém o CPF enviado na requisição POST
        cpf = request.POST.get('cpf')
        # Verifica se existe um cliente com o CPF fornecido
        if clientes.objects.filter(cpf=cpf).exists():
            # Se o CPF já existe, retorna um JSON indicando sua existência
            return JsonResponse({'exists': True})
    # Se o CPF não existe, retorna um JSON indicando sua não existência
    return JsonResponse({'exists': False})

#####################################################################################################################

@login_required(login_url='/')
def cadastro_externo(request):
    mensagem_erro = None

    if request.method == 'POST':
        cpf = request.POST.get('cpf')
        # Verifica se já existe um cliente com o mesmo CPF
        if clientes.objects.filter(cpf=cpf).exists():
            # Se o CPF já existir, atribua a mensagem de erro
            mensagem_erro = 'Este CPF já está em uso.'
        else:
            # Se o CPF não existir, crie um novo cliente
            cliente = clientes()
            # Preenche os campos do cliente com os dados do formulário
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
            # Salva o novo cliente no banco de dados
            cliente.save()

    # Obtém todos os clientes existentes
    clientes_data = {
        'clientes': clientes.objects.all(),
        # Adiciona a mensagem de erro ao contexto, para ser exibida no template
        'mensagem_erro': mensagem_erro  
    }
    # Renderiza a página de cadastro com os dados dos clientes e a mensagem de erro, se houver
    return render(request, 'internos/cadastro_externo.html', clientes_data)

#####################################################################################################################

@login_required(login_url='/')
def cadastro_financeiro(request):
   if request.method == 'POST':
       cpf = request.POST.get('cpf')
       # Verifica se o cliente com o CPF fornecido existe
       if clientes.objects.filter(cpf=cpf).exists():
           cliente = clientes.objects.get(cpf=cpf)
           # Cria um novo registro de cadastro financeiro e associa ao cliente
           cadastro = CadastroFinanceiro()
           cadastro.cliente = cliente
           # Preenche os campos do cadastro financeiro com os dados do formulário
           cadastro.cpf = request.POST.get('cpf')
           cadastro.valor = request.POST.get('valor')
           cadastro.data_pagamento = request.POST.get('data_pagamento')
           cadastro.forma_pagamento = request.POST.get('forma_pagamento')
           cadastro.chave_seguranca = request.POST.get('chave_seguranca')
           cadastro.departamento = request.POST.get('departamento')
           cadastro.descricao = request.POST.get('descricao')
           cadastro.save()
           # Redireciona para uma página de sucesso ou faça o que for necessário
       else:
           return HttpResponse('Cliente não encontrado.')
   # Se o método da requisição não for POST, apenas renderize o template
   return render(request, 'internos/cadastro_financeiro.html')

#####################################################################################################################

@login_required(login_url=('/'))   
def lista_clientes(request):
    cliente = {
        'cliente': clientes.objects.all()
    }
    return render(request, 'internos/lista_clientes.html', cliente)

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
        return redirect('plataforma')  # Substitua 'nome_da_view' pelo nome da view que renderiza a página

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
            return HttpResponseRedirect('/lista_usuarios')

        elif action == 'change_group':

            group_id = request.POST.get('group')
            group = Group.objects.get(pk=group_id)
            usuario = User.objects.get(pk=usuario_id)
            usuario.groups.add(group)
            messages.success(request, f'Grupo de {usuario.username} alterado para {group.name}.')
            return HttpResponseRedirect('/lista_usuarios')
        
        elif action == 'delete_usuario':

            usuario = User.objects.get(pk=usuario_id)
            usuario.delete()
            return HttpResponseRedirect('/lista_usuarios')
        
        elif action == 'reset_password':

            usuario = User.objects.get(pk=usuario_id)
            send_password_reset_email(request, usuario)
            messages.success(request, f'E-mail de redefinição de senha enviado para {usuario.username}.')
            return HttpResponseRedirect('/lista_usuarios')

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

@login_required(login_url=('/'))
def teste_cliente(request):
    if request.user.groups.filter(name='ADM').exists() | request.user.groups.filter(name='Secretaria').exists():
        # Se o usuário pertencer ao grupo "ADM", ele pode ver todos os serviços
        projeto = {
            'projeto': CadastroFinanceiro.objects.all()
        }
    else:
        # Caso contrário, ele só pode ver os serviços relacionados aos grupos aos quais pertence
        grupos_do_usuario = request.user.groups.all()
        departamentos_do_usuario = [grupo.name for grupo in grupos_do_usuario]
        projeto = {
            'projeto': CadastroFinanceiro.objects.filter(departamento__in=departamentos_do_usuario)
        }
    return render(request, 'internos/teste_cliente.html', projeto)

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

            # Convertendo datas de string para objetos datetime
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')

            if request.user.groups.filter(name='ADM').exists() | request.user.groups.filter(name='Secretaria').exists():
                # Se o usuário pertencer ao grupo "ADM", ele pode ver todos os serviços
                dados_filtrados = CadastroFinanceiro.objects.filter(data_pagamento__range=(data_inicio, data_fim))
            else:
                # Caso contrário, ele só pode ver os serviços relacionados ao seu grupo
                grupos_do_usuario = request.user.groups.all()
                departamentos_do_usuario = [grupo.name for grupo in grupos_do_usuario]
                dados_filtrados = CadastroFinanceiro.objects.filter(data_pagamento__range=(data_inicio, data_fim), departamento__in=departamentos_do_usuario)

            # Construindo o conteúdo do arquivo CSV
            csv_content = "CPF,Nome,CEP,Endereço,Número,Complemento,Bairro,Cidade,Estado,Telefone principal,E-mail,Valor,Data Pagamento,Forma Pagamento,Chave Segurança,Departamento\n"
            for dado in dados_filtrados:
                cliente = clientes.objects.get(cpf=dado.cpf)
                csv_content += f"{cliente.cpf},{cliente.nome},{cliente.cep},{cliente.endereco},{cliente.numero},{cliente.complemento},{cliente.bairro},{cliente.cidade},{cliente.estado},{cliente.telefone_principal},{cliente.email},{dado.valor},{dado.data_pagamento},{dado.forma_pagamento},{dado.chave_seguranca},{dado.departamento}\n"

            # Criando a resposta HTTP com o conteúdo CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="dados_exportados.csv"'
            response.write(csv_content)
            return response