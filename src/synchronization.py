import os
import shutil
import logging
from typing import List
import concurrent.futures

logger = logging.getLogger(__name__)


def replica_directory_is_empty(replica_path:str) -> bool:
    return len(os.listdir(replica_path)) == 0


def source_directory_not_empty(source_path:str) -> bool:
    return len(os.listdir(source_path)) >= 0


def copy_file(source_path: str, replica_path: str) -> None:
    if os.path.isfile(source_path):
        shutil.copy2(src=source_path, dst=replica_path) 
        logging.info(f"[COPIED] File: {source_path} -> {replica_path}")

    else:
        shutil.copy2(src=source_path, dst=replica_path) 
        logging.info(f"[COPIED] Directory: {source_path} -> {replica_path}")


def delete_extra_files(replica_path: str) -> None:
    if os.path.isfile(replica_path):
        os.remove(path=replica_path)
        logging.info(f"[DELETED] File: {replica_path}")

    elif os.path.isdir(replica_path):
        shutil.rmtree(path=replica_path)
        logging.info(f"[DELETED] Directory: {replica_path}")


def duplicate_source(source_directory_path:str, replica_directory_path:str) -> None:
    if not os.path.exists(replica_directory_path):
        os.makedirs(replica_directory_path)
        logging.info(f"[CREATED] Directory: {replica_directory_path}")


    def copy_item(item_path: str, base_source: str, base_replica: str) -> None:
        relative_path:str = os.path.relpath(path=item_path, start=base_source)
        target_path:str = os.path.join(base_replica, relative_path)

        if os.path.isdir(item_path):
            if not os.path.exists(target_path):
                os.makedirs(target_path)
                logging.info(f"[CREATED] Directory: {target_path}")

        else:
            shutil.copy2(item_path, target_path)
            logging.info(f"[CREATED] File: {item_path} -> {target_path}")


    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures:List[concurrent.futures.Future] = []
        for root, dirs, files in os.walk(source_directory_path):
            for name in dirs + files:
                item_path:str = os.path.join(root, name)
                futures.append(executor.submit(copy_item, item_path, source_directory_path, replica_directory_path))
        
        concurrent.futures.wait(futures)        


def update_replica_directory(source_directory_path: str, replica_directory_path: str) -> None:

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures:List[concurrent.futures.Future] = []

        # Loop through the source directory and update the replica
        for root, dirs, files in os.walk(source_directory_path, topdown=True):
            for file in files:
                source_file:str = os.path.normpath(os.path.join(root, file))
                relative_file_path:str = os.path.normpath(os.path.relpath(path=source_file, start=source_directory_path))
                replica_file:str = os.path.normpath(os.path.join(replica_directory_path, relative_file_path))

                if not os.path.exists(replica_file):
                    futures.append(executor.submit(copy_file, source_file, os.path.join(replica_directory_path, relative_file_path)))

                elif (os.stat(source_file).st_mtime) > (os.stat(os.path.join(replica_directory_path, relative_file_path)).st_mtime):
                    futures.append(executor.submit(copy_file, source_file, replica_file))


            for dir in dirs:
                source_dir:str = os.path.normpath(os.path.join(root, dir))
                relative_path:str = os.path.normpath(os.path.relpath(path=source_dir, start=source_directory_path))
                replica_dir:str = os.path.normpath(os.path.join(replica_directory_path, relative_path))
                
                if not os.path.exists(replica_dir):
                    os.makedirs(replica_dir)
                    logging.info(f"[CREATED] directory: {replica_dir}")

                if os.stat(source_dir).st_mtime > os.stat(replica_dir).st_mtime:
                    futures.append(executor.submit(copy_file, source_dir, replica_dir))


                    
        # Search for files that do not match the source
        for root, dirs, files in os.walk(replica_directory_path, topdown=False):
            for name in files:
                replica_file:str = os.path.normpath(os.path.join(root, name))
                source_file:str = os.path.normpath(os.path.join(source_directory_path, os.path.relpath(path=replica_file, start=replica_directory_path)))

                if not os.path.exists(source_file):
                    futures.append(executor.submit(delete_extra_files, replica_file))

            for name in dirs:
                replica_dir:str = os.path.normpath(os.path.join(root, name))
                source_dir:str = os.path.normpath(os.path.join(source_directory_path, os.path.relpath(path=replica_dir, start=replica_directory_path)))

                if not os.path.exists(source_dir):
                    futures.append(executor.submit(delete_extra_files, replica_dir))

        concurrent.futures.wait(futures)


def synchronize(source_directory_path:str, replica_directory_path:str, changes:list) -> None:
    for change in changes:
        rel_path:str = os.path.relpath(change['path'], source_directory_path)
        dst_path:str = os.path.join(replica_directory_path, rel_path)

        if change['type'] == 'created':
            try:
                if os.path.isfile(change['path']):
                    shutil.copy2(src=change['path'], dst=dst_path) 
                    logging.info(f"[CREATED] File: {dst_path}")
                else:
                    shutil.copytree(change['path'], dst_path)
                    logging.info(f"[CREATED] Directory: {dst_path}")

            except Exception as e:
                logging.error(f"[ERROR] Creating {'file' if os.path.isfile(change['path']) else 'directory'}. Error: {e}")
                update_replica_directory(source_directory_path, replica_directory_path)
                logging.info("[FIXED] Error fixed")


        elif change['type'] == 'deleted':
            try:
                if change['is_file']:
                    os.remove(dst_path)
                    logging.info(f"[DELETED] File: {os.path.normpath(dst_path)}")
                else:
                    shutil.rmtree(dst_path)
                    logging.info(f"[DELETED] Directory: {os.path.normpath(dst_path)}")
            except Exception as e:
                logging.error(f"[ERROR] Deleting {'file' if change['is_file'] else 'directory'}. Error: {e}")
                update_replica_directory(source_directory_path, replica_directory_path)
                logging.info("[FIXED] Error fixed")


        elif change['type'] == 'renamed':
            try:
                relative_src_path = os.path.relpath(change['path'], source_directory_path)
                relative_dest_path = os.path.relpath(change['new_path'], source_directory_path)

                old_name_path = os.path.join(replica_directory_path, relative_src_path)
                new_name_path = os.path.join(replica_directory_path, relative_dest_path)

                if change['is_file']:
                    if os.path.exists(old_name_path):
                        os.rename(old_name_path, new_name_path)
                        logging.info(f"[RENAMED] File: {old_name_path} -> {new_name_path}")

                    else:
                        continue

                else:
                    os.rename(dst_path, change['path'])
                    logging.info(f"[RENAMED] Directory: {os.path.normpath(old_name_path)} -> {os.path.normpath(new_name_path)}")

            except Exception as e:
                logging.error(f"[ERROR] Renaming {'file' if change['is_file'] else 'directory'}. Error: {e}")
                update_replica_directory(source_directory_path, replica_directory_path)
                logging.info("[FIXED] Error fixed")



        elif change['type'] == 'moved':
            source_path:str = os.path.join(replica_directory_path, os.path.relpath(change['path'], source_directory_path))
            destination_path:str = os.path.join(replica_directory_path, os.path.join(os.path.relpath(change['new_path'], source_directory_path), os.path.basename(change['path'])))

            try:
                if change['is_file']:
                    shutil.move(source_path, destination_path)
                    logging.info(f"[MOVED] File: {source_path} -> {destination_path}")

                else:
                    shutil.move(source_path, destination_path)
                    logging.info(f"[MOVED] Directory: {source_path} -> {destination_path}")

            except Exception as e:
                logging.error(f"[ERROR] Moving {'file' if change['is_file'] else 'directory'}. Error: {e}")
                update_replica_directory(source_directory_path, replica_directory_path)
                logging.info("[FIXED] Error fixed")


        elif change['type'] == 'modified':
            if os.path.isfile(change['path']):
                try:
                    shutil.copy2(src=change['path'], dst=dst_path) 
                    logging.info(f"[MODIFIED] File: {dst_path}")
    
                except Exception as e:
                    logging.error(f"[ERROR] Editing file: {dst_path}. Error: {e}")
                    update_replica_directory(source_directory_path, replica_directory_path)
                    logging.info("[FIXED] Error fixed")




