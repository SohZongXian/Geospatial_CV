import os
import multiprocessing
from PIL import Image
import os
from osgeo import gdal
import multiprocessing

def generate_tile(input_file, output_dir, grid_x, grid_y, i, j):
    ds = gdal.Open(input_file)

    # Get image size and number of bands
    width = ds.RasterXSize
    height = ds.RasterYSize
    num_bands = ds.RasterCount

    x_offset = i * grid_x
    y_offset = j * grid_y

    tile_width = min(grid_x, width - x_offset)
    tile_height = min(grid_y, height - y_offset)

    tile = []
    for band in range(1, num_bands + 1):
        tile_data = ds.GetRasterBand(band).ReadAsArray(x_offset, y_offset, tile_width, tile_height)
        tile.append(tile_data)

    # Create output filename
    output_file = os.path.join(output_dir, f"tile_{i}_{j}.tif")

    # Create an output TIFF file with same CRS and band values range
    driver = gdal.GetDriverByName("GTiff")
    options = ['COMPRESS=DEFLATE', 'PREDICTOR=2', 'TILED=YES']
    out_ds = driver.Create(output_file, tile_width, tile_height, num_bands,
                           ds.GetRasterBand(1).DataType, options=options)

    # Set the geotransform
    geotransform = list(ds.GetGeoTransform())
    geotransform[0] = geotransform[0] + x_offset * geotransform[1]
    geotransform[3] = geotransform[3] + y_offset * geotransform[5]
    out_ds.SetGeoTransform(tuple(geotransform))

    # Set the projection
    out_ds.SetProjection(ds.GetProjection())

    # Write each band to the output file
    for band in range(1, num_bands + 1):
        out_band = out_ds.GetRasterBand(band)
        out_band.WriteArray(tile[band - 1])

    # Close the output file
    out_ds = None

def generate_tiles(input_file, output_dir, grid_x, grid_y):
    ds = gdal.Open(input_file)

    # Get image size and number of bands
    width = ds.RasterXSize
    height = ds.RasterYSize

    # Calculate number of tiles in each dimension
    num_tiles_x = (width // grid_x)
    num_tiles_y = (height // grid_y)

    print(f"Total number of tiles: {num_tiles_x * num_tiles_y}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Number of parallel processes
    num_processes = multiprocessing.cpu_count()

    # Create a process pool
    pool = multiprocessing.Pool(processes=num_processes)

    # Iterate over each tile and submit it as a job to the pool
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            pool.apply_async(generate_tile, args=(input_file, output_dir, grid_x, grid_y, i, j))

    # Close the pool and wait for all processes to finish
    pool.close()
    pool.join()

    print("Tiles generation completed.")



def convert_tiff_to_jpeg_worker(input_file, output_dir):
    img = Image.open(input_file)

    # check if image is RGB mode, if not convert it
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # create new filename, replace .tif with .jpg
    output_filename = os.path.splitext(os.path.basename(input_file))[0] + '.jpg'

    # save the image in JPEG format
    img.save(os.path.join(output_dir, output_filename), 'JPEG')

    
def convert_tiff_to_jpeg(input_dir, output_dir):
    # check if output_dir exists, if not create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get list of tiff files
    tiff_files = [os.path.join(input_dir, filename) for filename in os.listdir(input_dir) if filename.endswith('.tif')]

    # Number of parallel processes
    num_processes = multiprocessing.cpu_count()

    # Create a process pool
    pool = multiprocessing.Pool(processes=num_processes)

    # Apply the worker function to each file
    pool.starmap(convert_tiff_to_jpeg_worker, [(file, output_dir) for file in tiff_files])

    # Close the pool
    pool.close()
    pool.join()

    print("Conversion from TIFF to JPEG completed.")
