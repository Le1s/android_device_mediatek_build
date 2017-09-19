#! /usr/bin/env python
__author__ = 'mtk'
import sys
import os

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hc:k:p:b:l:m:", ["help", "prjconfig=", "kconfig=", "project=", "preloader=", "lk=", "md32="])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    prjConfig, kConfig, project, plConfig, lkConfig, md32Config = parse_opt(opts)
    if not prjConfig or not project:
        Usage()
    if not kConfig and not plConfig and not lkConfig and not md32Config:
        Usage()

    check_path(prjConfig)
    prj_option = get_projectConfiguration(prjConfig)
    reCode = 0

    if kConfig:
        check_path(kConfig)
        k_option = get_kconfig(kConfig)
        reCode += run_gen_defconfig(prj_option, k_option)
    if plConfig:
        check_path(plConfig)
        pl_option = get_pl_config(plConfig)
        reCode += run_check_pl_config(prj_option, pl_option)
    if lkConfig:
        check_path(lkConfig)
        lk_option = get_lk_config(lkConfig)
        reCode += run_check_lk_config(prj_option, lk_option)
    if md32Config:
        check_path(md32Config)
        md32_option = get_md32_config(md32Config)
        reCode += run_check_md32_config(prj_option, md32_option)

    sys.exit(reCode)


def check_path(path):
    if not os.path.exists(path):
        print >> sys.stderr, "Error Can not find out the file" % path
        sys.exit(12)


def parse_opt(opts):
    prjconfig = ""
    kconfig = ""
    project = ""
    plconfig = ""
    lkconfig = ""
    md32config = ""
    for opt, arg in opts:
        if opt in ("-c", "--prjconfig"):
            prjconfig = arg
        if opt in ("-k", "--kconfig"):
            kconfig = arg
        if opt in ("-p", "--project"):
            project = arg
        if opt in ("-b", "--preloader"):
            plconfig = arg
        if opt in ("-l", "--lk"):
            lkconfig = arg
        if opt in ("-m", "--md32"):
            md32config = arg
        if opt in ("-h", "--help"):
            Usage()
    return prjconfig, kconfig, project, plconfig, lkconfig, md32config


def get_projectConfiguration(prjConfig):
    """query the current platfomr"""
    pattern = [re.compile("^([^=\s]+)\s*=\s*(.+)$"),
               re.compile("^([^=\s]+)\s*=$")]
    config = {}
    ff = open(prjConfig, "r")
    for line in ff.readlines():
        result = (filter(lambda x: x, [x.search(line) for x in pattern]) or [None])[0]
        if not result: continue
        name, value = None, None
        if len(result.groups()) == 0: continue
        name = result.group(1)
        try:
            value = result.group(2)
        except IndexError:
            value = ""
        config[name] = value.strip()
        #for debug
        #print >> sys.stdout, "config name:%s config value: %s \n" % (name, value)
    return config


def run_gen_defconfig(prjOption, kOption):
    """Generate defconfig options base on ProjectConfig.mk"""

    genKconfig = []
    return_code = 0
    for i in prjOption:
        #print >>sys.stdout,'config_NAME:%s config_VALUE:%s' % (i,prjOption[i])
        if prjOption[i] == 'yes':
            #print 'CONFIG_' + i + '=y'
            #genKconfig.append('CONFIG_' + i + '=y')
            if 'CONFIG_'+i in kOption:
                if kOption['CONFIG_'+i] != 'y':
                    print >> sys.stdout, "Kconfig Setting: %s" % kOption['CONFIG_'+i]
                    print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                    print >> sys.stdout, "*** Boolean ERROR ***: CONFIG_%s not sync with %s in ProjectConfig.mk " % (i,i)
                    return_code += 1
        elif prjOption[i] == 'no':
            #print >>sys.stdout, '# CONFIG_' + i + ' is not set'
            #genKconfig.append('# CONFIG_' + i + ' is not set')
            if 'CONFIG_'+i in kOption:
                if kOption['CONFIG_'+i] != 'is not set':
                    print >> sys.stdout, "Kconfig Setting: %s" % kOption['CONFIG_'+i]
                    print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                    print >> sys.stdout, "*** Boolean ERROR ***: CONFIG_%s not sync with %s in ProjectConfig.mk" % (i,i)
                    return_code += 1
        elif prjOption[i] =='':
            if 'CONFIG_'+i in kOption:
                if kOption['CONFIG_'+i] != 'is not set' and  kOption['CONFIG_'+i] != '\"\"':
                    print >> sys.stdout, "Kconfig Setting: %s" % kOption['CONFIG_'+i]
                    print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                    print >> sys.stdout, "*** Boolean ERROR ***: CONFIG_%s not sync with %s in ProjectConfig.mk" % (i,i)
                    return_code += 1

        elif prjOption[i].isdigit():
            #print >> sys.stdout, 'CONFIG_' + i + '=%s' % prjOption[i]
            #genKconfig.append('CONFIG_' + i + '=%s' % prjOption[i])
            if 'CONFIG_'+i in kOption:
                if kOption['CONFIG_'+i] != prjOption[i] and kOption['CONFIG_'+i] != '\"'+prjOption[i]+'\"':
                    print >> sys.stdout, "Kconfig Setting: %s" % kOption['CONFIG_'+i]
                    print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                    print >> sys.stdout, "***Int ERROR ***: CONFIG_%s not sync with %s in ProjectConfig.mk" % (i,i)
                    return_code += 1
        elif len(prjOption[i]) > 0:
            pattern = re.compile('^0x\w*')
            match = pattern.match(prjOption[i])
            if match:
                #print >> sys.stdout, 'CONFIG_' + i + '=%s' % prjOption[i]
                #genKconfig.append('CONFIG_' + i + '=%s' % prjOption[i])
                if 'CONFIG_'+i in kOption:
                    if for_hex_parsing(kOption['CONFIG_'+i]) != for_hex_parsing(prjOption[i]) and kOption['CONFIG_'+i] != '\"'+prjOption[i]+'\"':
                        print >> sys.stdout, "Kconfig Setting: %s" % kOption['CONFIG_'+i]
                        print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                        print >> sys.stdout, "*** Hex ERROR ***: CONFIG_%s not sync with %s in ProjectConfig.mk" % (i,i)
                        return_code += 1
            else:
                #print >> sys.stdout, 'CONFIG_'+i+'=\"%s\"' % prjOption[i]
                #genKconfig.append('CONFIG_'+i+'\"=%s\"' % prjOption[i])
                if 'CONFIG_'+i in kOption:
                    if kOption['CONFIG_'+i].lower() != '\"'+prjOption[i].lower()+'\"' and kOption['CONFIG_'+i] !='y':
                        print >> sys.stdout, "Kconfig Setting: %s" % kOption['CONFIG_'+i]
                        print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                        print >> sys.stdout, "*** String ERROR ***: CONFIG_%s not sync with %s in ProjectConfig.mk" % (i,i)
                        return_code += 1
    return return_code


def run_check_pl_config(prjOption, plOption):
    return_code = 0
    for i in prjOption:
        if i in plOption:
            if plOption[i] != prjOption[i]:
                print >> sys.stdout, "Preloader config Setting: %s" % plOption[i]
                print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                print >> sys.stdout, "*** String ERROR ***: %s not sync with %s in ProjectConfig.mk " % (i,i)
                return_code += 1
    return return_code


def run_check_lk_config(prjOption, lkOption):
    return_code = 0
    for i in prjOption:
        if i in lkOption:
            if lkOption[i] != prjOption[i]:
                print >> sys.stdout, "LK config Setting: %s" % lkOption[i]
                print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                print >> sys.stdout, "*** String ERROR ***: %s not sync with %s in ProjectConfig.mk " % (i,i)
                return_code += 1
    return return_code


def run_check_md32_config(prjOption, md32Option):
    return_code = 0
    for i in prjOption:
        if i in md32Option:
            if md32Option[i] != prjOption[i]:
                print >> sys.stdout, "MD32 config Setting: %s" % md32Option[i]
                print >> sys.stdout, "ProjectConfig Setting: %s" % prjOption[i]
                print >> sys.stdout, "*** String ERROR ***: %s not sync with %s in ProjectConfig.mk " % (i,i)
                return_code += 1
    return return_code


def for_hex_parsing(hex):
    pattern = re.compile("0x[0]*([A-Za-z1-9]+0*)")
    match= pattern.match(hex)
    if match:
        return match.group(1)


def get_kconfig(kconfig):
    """read all the kernel config for furture comparasion
    direct use the comparation result as error message"""

    kconfig_option={}
    pattern = [re.compile("^([^=\s]+)\s*=\s*(.+)$"),
               re.compile("^#\s(\w+) is not set")]
    ff = open(kconfig,'r')
    for line in ff.readlines():
        result = (filter(lambda x: x, [x.search(line) for x in pattern]) or [None])[0]
        if not result: continue
        name, value = None, None
        if len(result.groups()) == 0: continue
        name = result.group(1)
        try:
            value = result.group(2)
        except IndexError:
             value = " is not set"
        kconfig_option[name] = value.strip()
        #for debug
        #print >> sys.stdout, "config name:%s config value: %s \n" % (name, value)
    return kconfig_option


def get_pl_config(plConfig):
    pattern = [re.compile("^([^\#\:=\s]+)\s*\:?=\s*(.*)$")]
    config = {}
    ff = open(plConfig, "r")
    for line in ff.readlines():
        result = (filter(lambda x: x, [x.search(line) for x in pattern]) or [None])[0]
        if not result: continue
        name, value = None, None
        if len(result.groups()) == 0: continue
        name = result.group(1)
        try:
            value = result.group(2)
        except IndexError:
            value = ""
        config[name] = value.strip()
    return config


def get_lk_config(lkConfig):
    return get_pl_config(lkConfig)


def get_md32_config(md32Config):
    return get_pl_config(md32Config)


def Usage():
    print """Usage:
                   -h, --help=:          show the Usage of commandline argments;
                   -c, --prjconfig=:     project configuration path;
                   -k, --kconfig=:       kconfiguration path;
                   -b, --preloader=:     preloader configuration path;
                   -l, --lk=:            lk configuration path;
                   -m, --md32=:          md32 configuration path;
                   -p, --project=:       check project.
example:
                   python check_kernel_config.py -c $prjconfig_path -k $kconfig_path -b $pl_path -l $lk_path -p $project
                   python check_kernel_config.py --prjconfig $prjconfig_path --kconfig $kconfig_path --preloader $pl_path --lk $lk_path --poject $project
          """
    sys.exit(1)


if __name__ == "__main__":
    import os, sys, re, getopt, commands, string
    import xml.dom.minidom as xdomxdom
    main(sys.argv[1:])
