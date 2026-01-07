import json
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from settings import *

def clear_screen():
    os.system("cls")

def start_browser(link=link_default):
    clear_screen()
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.binary_location = chrome_binary_path
    options.add_argument("--headless")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("log-level=3")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(link)

        # data = {}
        data = []
        all_links_from_table = extract_links_from_table(driver=driver)
        
        for i, link in enumerate(all_links_from_table):
            driver.get(link)
            os.system("cls")
            print(f"[{i+1}/{len(all_links_from_table)}] Scanning...")
            src = driver.page_source
            soup = BeautifulSoup(src, "html.parser")


            current_faculty = ""
            should_we_skip = True
            for item in soup.find_all("h6"):
                if "бюджетная основа" in item.text.lower():
                    should_we_skip = False
                    current_faculty = soup.find_all("h6")[1].text.split("-")[1].strip()
                    break
            
            if should_we_skip: continue
            
            all_table_rows = soup.find("tbody").find_all("tr")

            for row in all_table_rows:
                all_row_columns = row.find_all("td")

                data_piece = {}
                data_unique_code = all_row_columns[1].text
                data_priority = all_row_columns[2].text
                data_total_points = all_row_columns[3].text
                data_total_points_by_subjects = all_row_columns[4].text
                data_total_points_by_additions = all_row_columns[5].text
                data_state = all_row_columns[6].text
                data_document_type = all_row_columns[7].text
                data_financing_source = all_row_columns[8].text
                data_direction = all_row_columns[9].text
                data_target = all_row_columns[10].text
                data_without_entrance_tests = all_row_columns[11].text
                data_special_rights = all_row_columns[12].text
                data_olympiad = all_row_columns[13].text

                # if not data.get(data_unique_code):
                if not any([item for item in data if item["ID"] == data_unique_code]):
                    data_piece = {}
                    data_piece["ID"] = data_unique_code
                    data_piece["Сумма баллов"] = int(data_total_points)
                    data_piece["Факультеты"] = [{
                        "Приоритет": int(data_priority),
                        "Название факультета": current_faculty,
                        "Направление\специальность": data_direction,
                        "Целевик": data_target,
                        "Без вступительных испытаний (олимпиадник)": data_without_entrance_tests,
                        "Особые права": data_special_rights,
                        "Олимпиада": []
                    }]
                    if data_olympiad: data_piece["Факультеты"][0]["Олимпиада"] = [data_olympiad]
                    # data_piece["Сумма баллов по предметам"] = int(data_total_points_by_subjects)
                    # data_piece["Сумма баллов за инд.дост.(конкурсные)"] = int(data_total_points_by_additions)
                    # data_piece["Состояние"] = data_state
                    data_piece["Вид документа"] = data_document_type
                    data_piece["Источник финансирования"] = data_financing_source
                    # data_piece["Направление\специальность"] = data_direction
                    # data_piece["Целевик"] = data_target
                    # data_piece["Без вступительных испытаний (олимпиадник)"] = data_without_entrance_tests
                    # data_piece["Особые права"] = data_special_rights
                    # data_piece["Олимпиада"] = data_olympiad

                    # data[data_unique_code] = data_piece
                    data.append(data_piece)
                else:
                    new_faculty = {
                        "Приоритет": int(data_priority),
                        "Название факультета": current_faculty,
                        "Направление\специальность": data_direction,
                        "Целевик": data_target,
                        "Без вступительных испытаний (олимпиадник)": data_without_entrance_tests,
                        "Особые права": data_special_rights,
                        "Олимпиада": []
                    }
                    if data_olympiad: new_faculty["Олимпиада"] = [data_olympiad]
                    id_in_data = [i for i, item in enumerate(data) if item["ID"] == data_unique_code][0]

                    if new_faculty["Название факультета"] in [item["Название факультета"] for item in data[id_in_data]["Факультеты"]]:
                        temp_required_faculty_id = [i for i, item in enumerate(data[id_in_data]["Факультеты"]) if new_faculty["Название факультета"] == item["Название факультета"]][0]
                        if data_olympiad not in data[id_in_data]["Факультеты"][temp_required_faculty_id]["Олимпиада"]:
                            data[id_in_data]["Факультеты"][temp_required_faculty_id]["Олимпиада"].append(data_olympiad)
                    else:
                        data[id_in_data]["Факультеты"].append(new_faculty)

                    # if new_faculty not in data[data_unique_code]["Факультеты"]:
                    #     temp_faculties = data[data_unique_code]["Факультеты"]
                    #     temp_faculties.append(new_faculty)
                    #     temp_faculties.sort(key=lambda x: x["Приоритет"])
                    #     data[data_unique_code]["Факультеты"] = temp_faculties

        data.sort(key=lambda x: x["Сумма баллов"], reverse=True)
        [item["Факультеты"].sort(key=lambda x: x["Приоритет"]) for item in data]

        save_results_into_json(data=data, filename="data")

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()

def save_results_into_json(data, filename):
    clear_screen()
    with open(f"{filename}.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"{len(data)} rows were saved!")

def extract_links_from_table(driver):
    all_table_rows = driver.find_elements(By.TAG_NAME, "tr")
    all_link_tags_from_table = [row.find_elements(By.TAG_NAME, "a") for row in all_table_rows]
    all_link_tags_from_table.sort(key=lambda x: x != [], reverse=True)
    all_link_tags_from_table = all_link_tags_from_table[:all_link_tags_from_table.index([])]
    all_links_from_table = [tag[0].get_attribute("href") for tag in all_link_tags_from_table]
    return all_links_from_table