from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django import forms
from django.db.models import Q
from django.http import JsonResponse
from .models import Sale
from .forms import SaleForm
import os
import uuid
import xml.etree.ElementTree as ET
import xml.dom.minidom
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def index(request):
    form = SaleForm()
    source = request.GET.get('source', 'xml')
    if source == 'db':
        sales = Sale.objects.all()
        xml_contents = [{'file': 'База данных', 'sales': [{'id': s.id, 'product': s.product, 'price': s.price, 'quantity': s.quantity, 'date': str(s.date)} for s in sales]}]
    else:
        xml_files = []
        xml_dir = os.path.join(settings.MEDIA_ROOT, 'xml_files')
        if os.path.exists(xml_dir):
            xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
        
        xml_contents = []
        for file in xml_files:
            try:
                tree = ET.parse(os.path.join(xml_dir, file))
                root = tree.getroot()
                sales = []
                for sale in root.findall('sale'):
                    data = {'id': sale.get('id')}
                    data['product'] = sale.find('product').text if sale.find('product') is not None else ''
                    data['price'] = sale.find('price').text if sale.find('price') is not None else ''
                    data['quantity'] = sale.find('quantity').text if sale.find('quantity') is not None else ''
                    data['date'] = sale.find('date').text if sale.find('date') is not None else ''
                    sales.append(data)
                xml_contents.append({'file': file, 'sales': sales})
            except ET.ParseError:
                xml_contents.append({'file': file, 'error': 'Невалидный XML'})

    context = {'form': form, 'xml_contents': xml_contents, 'has_files': bool(xml_contents), 'source': source}
    return render(request, 'sales_app/index.html', context)

def save_data(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            storage_type = data['storage_type']
            if storage_type == 'db':
                if Sale.objects.filter(product=data['product'], price=data['price'], quantity=data['quantity'], date=data['date']).exists():
                    return render(request, 'sales_app/index.html', {'error': 'Дубликат записи в БД. Данные не сохранены.'})
                Sale.objects.create(product=data['product'], price=data['price'], quantity=data['quantity'], date=data['date'])
            elif storage_type == 'xml':
                xml_dir = os.path.join(settings.MEDIA_ROOT, 'xml_files')
                os.makedirs(xml_dir, exist_ok=True)
                xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
                if xml_files:
                    file_name = xml_files[0]
                    file_path = os.path.join(xml_dir, file_name)
                    try:
                        tree = ET.parse(file_path)
                        root = tree.getroot()
                        if root.tag != 'sales':
                            logger.error(f"Неверный корневой тег в {file_name}: {root.tag}")
                            return redirect('sales_app:index')
                    except ET.ParseError:
                        logger.error(f"Ошибка парсинга {file_name}, создаём новый файл")
                        file_name = None
                else:
                    file_name = f"sales_{uuid.uuid4()}.xml"
                    file_path = os.path.join(xml_dir, file_name)
                    root = ET.Element('sales')

                if not xml_files or not file_name:
                    root = ET.Element('sales')
                    file_name = f"sales_{uuid.uuid4()}.xml"
                    file_path = os.path.join(xml_dir, file_name)

                sale = ET.SubElement(root, 'sale', id=str(uuid.uuid4()))
                ET.SubElement(sale, 'product').text = data['product']
                ET.SubElement(sale, 'price').text = str(data['price'])
                ET.SubElement(sale, 'quantity').text = str(data['quantity'])
                ET.SubElement(sale, 'date').text = data['date'].strftime('%Y-%m-%d')

                xml_str = ET.tostring(root, encoding='unicode')
                parsed = xml.dom.minidom.parseString(xml_str)
                pretty_xml = parsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(pretty_xml)
                logger.debug(f"Сохранено в {file_path}")
            return redirect('sales_app:index')
    return redirect('sales_app:index')

def edit_sale(request, pk):
    sale = Sale.objects.get(id=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale.product = form.cleaned_data['product']
            sale.price = form.cleaned_data['price']
            sale.quantity = form.cleaned_data['quantity']
            sale.date = form.cleaned_data['date']
            sale.save()
            return redirect('sales_app:index')
    else:
        form = SaleForm(initial={'product': sale.product, 'price': sale.price, 'quantity': sale.quantity, 'date': sale.date})
    return render(request, 'sales_app/edit.html', {'form': form, 'sale': sale})

def delete_sale(request, pk):
    sale = Sale.objects.get(id=pk)
    sale.delete()
    return redirect('sales_app:index')

def search_sales(request):
    query = request.GET.get('q', '')
    sales = Sale.objects.filter(Q(product__icontains=query))
    results = [{'id': s.id, 'product': s.product, 'price': s.price, 'quantity': s.quantity, 'date': str(s.date)} for s in sales]
    return JsonResponse({'sales': results})

def upload_xml(request):
    if request.method == 'POST' and 'xml_file' in request.FILES:
        xml_file = request.FILES['xml_file']
        if xml_file.name.endswith('.xml'):
            temp_file_name = f"temp_{uuid.uuid4()}.xml"
            temp_file_path = os.path.join(settings.MEDIA_ROOT, 'xml_files', temp_file_name)
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'xml_files'))
            fs.save(temp_file_name, xml_file)

            try:
                tree = ET.parse(temp_file_path)
                root = tree.getroot()
                if root.tag != 'sales':
                    os.remove(temp_file_path)
                    return render(request, 'sales_app/index.html', {'error': 'Невалидный XML: ожидается корневой тег <sales>'})

                # Проверка полей
                for sale in root.findall('sale'):
                    for field in ['product', 'price', 'quantity', 'date']:
                        if sale.find(field) is None:
                            os.remove(temp_file_path)
                            return render(request, 'sales_app/index.html', {'error': f'Невалидный XML: отсутствует поле {field}'})

                # Объединяем с основным файлом
                xml_dir = os.path.join(settings.MEDIA_ROOT, 'xml_files')
                xml_files = [f for f in os.listdir(xml_dir) if f.startswith('sales_') and f.endswith('.xml')]
                if xml_files:
                    main_file = xml_files[0]
                    main_path = os.path.join(xml_dir, main_file)
                    main_tree = ET.parse(main_path)
                    main_root = main_tree.getroot()
                else:
                    main_root = ET.Element('sales')
                    main_file = f"sales_{uuid.uuid4()}.xml"
                    main_path = os.path.join(xml_dir, main_file)

                # Копируем sale
                for sale in root.findall('sale'):
                    new_sale = ET.SubElement(main_root, 'sale', id=sale.get('id') or str(uuid.uuid4()))
                    for field in ['product', 'price', 'quantity', 'date']:
                        elem = sale.find(field)
                        if elem is not None:
                            ET.SubElement(new_sale, field).text = elem.text

                # Сохраняем с форматированием
                xml_str = ET.tostring(main_root, encoding='unicode')
                parsed = xml.dom.minidom.parseString(xml_str)
                pretty_xml = parsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
                with open(main_path, 'w', encoding='utf-8') as f:
                    f.write(pretty_xml)

                os.remove(temp_file_path)
                return redirect('sales_app:index')

            except ET.ParseError:
                os.remove(temp_file_path)
                return render(request, 'sales_app/index.html', {'error': 'Невалидный XML-файл'})
        else:
            return render(request, 'sales_app/index.html', {'error': 'Только XML-файлы'})
    return redirect('sales_app:index')